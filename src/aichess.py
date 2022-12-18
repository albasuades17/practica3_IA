#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 11:22:03 2022

@author: ignasi
"""

import random
from typing import List

import numpy as np

import chess

import json
import os

RawStateType = List[List[List[int]]]

from itertools import permutations


class Aichess():
    """
    A class to represent the game of chess.

    ...

    Attributes:
    -----------
    chess : Chess
        represents the chess game

    Methods:
    --------
    startGame(pos:stup) -> None
        Promotes a pawn that has reached the other side to another, or the same, piece

    """

    def __init__(self, TA, myinit=True):

        if myinit:
            self.chess = chess.Chess(TA, True)
        else:
            self.chess = chess.Chess([], False)

        self.listNextStates = []
        self.currentStateW = self.chess.boardSim.currentStateW
        self.qTable = {}
        self.qTableWhites = {}
        self.qTableBlacks = {}
        self.numVisitedWhites = {}
        self.numVisitedBlacks = {}
        self.kValue = 0
        self.errorValue = 0.5

    def checkMateList(self):
        #Fem una llista d'estats on en un moviment de la torre s'arriba a un checkMate
        #Per la manera que hem fet els estats, podem fixar que el rei negre estigui entre la columna 0 i 3 (inclosa).
        listCheckMates = []
        for columnaBk in range(0, 4):
            bkState = [0, columnaBk, 12]
            wkState = [2, columnaBk, 6]
            if columnaBk < 2:
                for columnaWr in range(columnaBk + 2, 8):
                    for filaWr in range(1, 8):
                        wrState = [filaWr, columnaWr, 2]
                        listCheckMates.append([wkState, bkState, wrState])
            else:
                for columnaWr in range(0, columnaBk -1):
                    for filaWr in range(1,8):
                        wrState = [filaWr, columnaWr, 2]
                        listCheckMates.append([wkState, bkState, wrState])
                for columnaWr in range(columnaBk + 2, 8):
                    for filaWr in range(1, 8):
                        wrState = [filaWr, columnaWr, 2]
                        listCheckMates.append([wkState, bkState, wrState])
        bkState = [0,0,12]
        wkState = [1,2,6]
        for i in range(2,8):
            for j in range(1,8):
                wrState = [i,j,2]
                listCheckMates.append([wkState, bkState, wrState])

        return listCheckMates

    def middleStatesList(self):
        #Posem estats on encara no hi hagi la torre negra perquè els dos jugadors aprenguin a jugar
        #En els estats proposats es va incrementant la dificultat.
        #També concretem els moviments màxims que deixarem fer per cada  configuració.
        listMiddleStates = []
        listMiddleStates.append(([[0, 2, 12], [1, 0, 2], [3, 4, 6]], 25))
        listMiddleStates.append(([[0, 1, 12], [1, 6, 2], [3, 4, 6]], 25))
        listMiddleStates.append(([[1, 2, 12], [2, 4, 2], [4, 4, 6]], 30))
        listMiddleStates.append(([[1, 1, 12], [2, 6, 2], [4, 6, 6]], 30))
        listMiddleStates.append(([[2, 3, 12], [3, 6, 2], [5, 4, 6]], 40))
        listMiddleStates.append(([[2, 5, 12], [3, 7, 2], [7, 4, 6]], 45))
        listMiddleStates.append(([[2, 4, 12], [0, 7, 2], [7, 4, 6]], 50))
        listMiddleStates.append(([[2, 6, 12], [0, 7, 2], [7, 4, 6]], 50))
        return listMiddleStates

    def stateToString(self, whiteState):
        wkState = self.getPieceState(whiteState,6)
        wrState = self.getPieceState(whiteState,2)
        stringState = str(wkState[0])+","+str(wkState[1])+","
        if wrState != None:
            stringState += str(wrState[0])+","+str(wrState[1])

        return stringState

    def stringToState(self, stringWhiteState):
        whiteState = []
        whiteState.append([int(stringWhiteState[0]),int(stringWhiteState[2]),6])
        if len(stringWhiteState) > 4:
            whiteState.append([int(stringWhiteState[4]),int(stringWhiteState[6]),2])

        return whiteState

    def BWStateToString(self, currentState):
        #Agafem l'estat de les peces
        wrState = self.getPieceState(currentState, 2)
        brState = self.getPieceState(currentState, 8)
        bkState = self.getPieceState(currentState, 12)
        wkState = self.getPieceState(currentState, 6)

        #Afegim les peces al listStates
        listStates = [bkState, wkState]
        listClassStates = []
        if wrState != None:
            listStates.append(wrState)
        if brState != None:
            listStates.append(brState)
        #A partir d'aquí crearem un representant únic per qualsevol configuració de les peces
        #Transformem respecte eix x si el rei negre està més abaix de la fila 3.
        #Fem la transformació per totes les peces, per tal que sigui un estat equivalent.
        if bkState[0] > 3:
            for state in listStates:
                listClassStates.append([7-state[0]])
        else:
            for state in listStates:
                listClassStates.append([state[0]])
        #Transformem respecte eix y si el rei negre está més endavant de la columna 3.
        if bkState[1] > 3:
            i = 0
            for state in listStates:
                listClassStates[i].append(7-state[1])
                i+=1
        else:
            i = 0
            for state in listStates:
                listClassStates[i].append(state[1])
                i += 1
        #Transformem respecte diagonal si la posició transformada del rei està per sota la diagonal.
        if listClassStates[0][1] < listClassStates[0][0]:
            i = 0
            for state in listStates:
                listClassStates[i][0], listClassStates[i][1] = listClassStates[i][1], listClassStates[i][0]
                i += 1

        #Fem simetries si el rei negre està a la diagonal. Això ho fem per fixar un estat representant.
        classBk = listClassStates[0]
        lenStates = len(listClassStates)
        if classBk[0] == classBk[1]:
            #Primer ho farem respecte l'estat del rei blanc
            classWk = listClassStates[1]
            if classWk[0] > classWk[1]:
                i = 0
                for state in listStates:
                    listClassStates[i][0], listClassStates[i][1] = listClassStates[i][1], listClassStates[i][0]
                    i += 1
            #Si l'estat del rei blanc també està a la diagonal, fixarem l'estat total amb una de les dues torres.
            elif classWk[0] == classWk[1]:
                if lenStates > 2:
                    classPiece = listClassStates[2]
                    if classPiece[0] > classPiece[1]:
                        i = 0
                        for state in listStates:
                            listClassStates[i][0], listClassStates[i][1] = listClassStates[i][1], listClassStates[i][0]
                            i += 1
                    elif classPiece[0] == classPiece[1]:
                        if lenStates > 3:
                            classPiece = listClassStates[3]
                            if classPiece[0] > classPiece[1]:
                                i = 0
                                for state in listStates:
                                    listClassStates[i][0], listClassStates[i][1] = listClassStates[i][1], \
                                                                                   listClassStates[i][0]
                                    i += 1
        #Un cop tenim l'estat representant, l'afem a piecesStateClass amb la numeració de cada peça
        piecesStateClass = [listClassStates[0]+[12],listClassStates[1]+[6]]
        i = 2
        if wrState != None:
            piecesStateClass.append(listClassStates[2]+[2])
            i+=1
        if brState != None:
            piecesStateClass.append(listClassStates[i] + [8])
        #Convertim aquesta configuració en una string única (tenim un ordre determinat de les peces)
        stringListStates = ""
        for state in piecesStateClass:
            pieceNumString = str(state[2])
            if state[2] == 12:
                pieceNumString = "x"
            stringListStates += str(state[0]) + str(state[1]) + pieceNumString
        return stringListStates

    def getCurrentStateW(self):

        return self.chess.boardSim.currentStateW

    def getListNextStatesW(self, myState):

        self.chess.boardSim.getListNextStatesW(myState)
        self.listNextStates = self.chess.boardSim.listNextStates.copy()

        return self.listNextStates

    def getListNextStatesB(self, myState):
        self.chess.boardSim.getListNextStatesB(myState)
        self.listNextStates = self.chess.boardSim.listNextStates.copy()

        return self.listNextStates

    def isWatchedBk(self, currentState):
        #Veiem si el rei negre està amenaçat
        self.newBoardSim(currentState)

        bkPosition = self.getPieceState(currentState, 12)[0:2]
        wkState = self.getPieceState(currentState, 6)
        wrState = self.getPieceState(currentState, 2)

        # Si les negres maten el rei blanc, no és una configuració correcta
        if wkState == None:
            return False
        # Mirem les possibles posicions del rei blanc i mirem si en alguna pot "matar" al rei negre
        for wkPosition in self.getNextPositions(wkState):
            if bkPosition == wkPosition:
                # Tindríem un checkMate
                return True
        if wrState != None:
            # Mirem les possibles posicions de la torre blanca i mirem si en alguna pot "matar" al rei negre
            for wrPosition in self.getNextPositions(wrState):
                if bkPosition == wrPosition:
                    return True

        return False

    def allBkMovementsWatched(self, currentState):
        # En aquest mètode mirem si el rei negre està amenaçat per les peces blanques

        self.newBoardSim(currentState)
        # Agafem l'estat del rei negre
        bkState = self.getPieceState(currentState, 12)
        allWatched = False
        # Rei negre es troba a una paret, llavors tots els seus moviments poden estar vigilats
        if bkState[0] == 0 or bkState[0] == 7 or bkState[1] == 0 or bkState[1] == 7:
            wrState = self.getPieceState(currentState, 2)
            whiteState = self.getWhiteState(currentState)
            allWatched = True
            # Obtenim els estats futur de les peces negres
            nextBStates = self.getListNextStatesB(self.getBlackState(currentState))

            for state in nextBStates:
                newWhiteState = whiteState.copy()
                # Comprovem si s'han menjat la torre blanca. En cas afirmatiu, la treiem de l'estat
                if wrState != None and wrState[0:2] == state[0][0:2]:
                    newWhiteState.remove(wrState)
                state = state + newWhiteState
                # Movem les peces negres al nou state
                self.newBoardSim(state)

                # Comprovem si en aquesta posició el rei negre no està amenaçat, que implica que no tots els seus moviments estan vigilats
                if not self.isWatchedBk(state):
                    allWatched = False
                    break
        self.newBoardSim(currentState)
        return allWatched

    def isBlackInCheckMate(self, currentState):
        if self.isWatchedBk(currentState) and self.allBkMovementsWatched(currentState):
            return True

        return False

    def isWatchedWk(self, currentState):
        #Veiem si el rei blanc està amenaçat

        self.newBoardSim(currentState)

        wkPosition = self.getPieceState(currentState, 6)[0:2]
        bkState = self.getPieceState(currentState, 12)
        brState = self.getPieceState(currentState, 8)

        # Si les blanques maten el rei negre, no és una configuració correcta
        if bkState == None:
            return False
        # Mirem les possibles posicions del rei negre i mirem si en alguna pot "matar" al rei blanc
        for bkPosition in self.getNextPositions(bkState):
            if wkPosition == bkPosition:
                # Tindríem un checkMate
                return True
        if brState != None:
            # Mirem les possibles posicions de la torre negra i mirem si en alguna pot "matar" al rei blanc
            for brPosition in self.getNextPositions(brState):
                if wkPosition == brPosition:
                    return True

        return False

    def allWkMovementsWatched(self, currentState):
        self.newBoardSim(currentState)
        # En aquest mètode mirem si el rei blanc està amenaçat per les peces negres
        # Agafem l'estat del rei blanc
        wkState = self.getPieceState(currentState, 6)
        allWatched = False
        # Rei blanc es troba a una paret, llavors es pot donar un checkMate
        if wkState[0] == 0 or wkState[0] == 7 or wkState[1] == 0 or wkState[1] == 7:
            # Obtenim l'estat de les nostres peces negres
            brState = self.getPieceState(currentState, 8)
            blackState = self.getBlackState(currentState)
            allWatched = True
            # Obtenim els estats futur de les peces blanques
            nextWStates = self.getListNextStatesW(self.getWhiteState(currentState))
            for state in nextWStates:
                newBlackState = blackState.copy()
                # Comprovem si s'han menjat la torre negra. En cas afirmatiu, treiem l'estat de la torre negra
                if brState != None and brState[0:2] == state[0][0:2]:
                    newBlackState.remove(brState)
                state = state + newBlackState
                # Movem les peces blanques al nou state
                self.newBoardSim(state)
                # Comprovem si en aquesta posició el rei blanc no està amenaçat, que implica que no tots els seus moviments estan vigilats
                if not self.isWatchedWk(state):
                    allWatched = False
                    break
        self.newBoardSim(currentState)
        return allWatched

    def isWhiteInCheckMate(self, currentState):
        if self.isWatchedWk(currentState) and self.allWkMovementsWatched(currentState):
            return True
        return False

    def newBoardSim(self, listStates):
        # Creem una nova boardSim
        TA = np.zeros((8, 8))
        for state in listStates:
            TA[state[0]][state[1]] = state[2]

        self.chess.newBoardSim(TA)

    def getPieceState(self, state, piece):
        pieceState = None
        for i in state:
            if i[2] == piece:
                pieceState = i
                break
        return pieceState

    def getCurrentState(self):
        listStates = []
        for i in self.chess.board.currentStateW:
            listStates.append(i)
        for j in self.chess.board.currentStateB:
            listStates.append(j)
        return listStates

    def getNextPositions(self, state):
        # Donat un estat, mirem els següents possibles estats
        # A partir d'aquests retornem una llista amb les posicions, és a dir, [fila,columna]
        if state == None:
            return None
        if state[2] > 6:
            nextStates = self.getListNextStatesB([state])
        else:
            nextStates = self.getListNextStatesW([state])
        nextPositions = []
        for i in nextStates:
            nextPositions.append(i[0][0:2])
        return nextPositions

    def getWhiteState(self, currentState):
        whiteState = []
        wkState = self.getPieceState(currentState, 6)
        whiteState.append(wkState)
        wrState = self.getPieceState(currentState, 2)
        if wrState != None:
            whiteState.append(wrState)
        return whiteState

    def getBlackState(self, currentState):
        blackState = []
        bkState = self.getPieceState(currentState, 12)
        blackState.append(bkState)
        brState = self.getPieceState(currentState, 8)
        if brState != None:
            blackState.append(brState)
        return blackState

    def getMovement(self, state, nextState):
        #Donat un estat i un estat successor, retornem la posició de la peça moguda en tots dos estats,
        pieceState = None
        pieceNextState = None
        for piece in state:
            if piece not in nextState:
                movedPiece = piece[2]
                pieceNext = self.getPieceState(nextState, movedPiece)
                if pieceNext != None:
                    pieceState = piece
                    pieceNextState = pieceNext
                    break

        return [pieceState, pieceNextState]

    def isCheckMate(self, mystate):
        #Check mate per l'exercici 1 (el rei negre està fixat a la posició [0,4]
        #posem els possibles estats on es produeixi check mate
        listCheckMateStates = [[[0,0,2],[2,4,6]],[[0,1,2],[2,4,6]],[[0,2,2],[2,4,6]],[[0,6,2],[2,4,6]],[[0,7,2],[2,4,6]]]

        #Mirem totes les permutacions de l'estat i si coincideixen amb la llista de CheckMates
        for permState in list(permutations(mystate)):
            if list(permState) in listCheckMateStates:
                return True

        return False

    def recompensa(self, mystate):
        #Recompensa per primer exercici
        if self.isCheckMate(mystate):
            return 100

        return -1

    def maxQValue(self, stringState, dictQValues):
        if stringState not in dictQValues.keys():
            return 0
        maxQ = -1000000
        dictState = dictQValues[stringState]
        for nextString in dictState.keys():
            maxQ = max(maxQ, dictState[nextString])
        return maxQ

    def epsilonState(self, epsilon, listStates, currentState):
        x = random.uniform(0,1)
        #Fem exploració amb probabilitat epsilon
        if x < epsilon:
            n = random.randint(0, len(listStates) - 1)
            nextState = listStates[n]
            nextString = self.stateToString(nextState)
            #Comprovem si l'estat s'ha visitat
            currentDict = self.qTable[self.stateToString(currentState)]
            if nextString not in currentDict.keys():
                currentDict[nextString] = 0
            return nextState, nextString
        #Fem explotació amb probabilitat 1 - epsilon
        else:
            listBestStates = []
            maxValue = float('-inf')
            currentDict = self.qTable[self.stateToString(currentState)]
            visitedStatesString = currentDict.keys()
            error = 0.1

            # Un primer bucle per trobar el màxim valor
            for state in listStates:
                stateString = self.stateToString(state)
                # Si l'estat no ha estat visitat, l'inicialitzem
                if stateString not in visitedStatesString:
                    currentDict[stateString] = 0
                qValue = currentDict[stateString]

                if qValue > maxValue:
                    maxValue = qValue
            # Un segnon bucle per trobar els millors estats
            for state in listStates:
                stateString = self.stateToString(state)
                qValue = currentDict[stateString]
                # Valorem si el valor es troba dins d'un marge d'error del major valor trobat
                # En cas afirmatiu, l'afegim als millors estats possibles
                if qValue >= maxValue - error:
                    listBestStates.append(state)

            n = random.randint(0,len(listBestStates)-1)
            selectedState = listBestStates[n]
            selectedString = self.stateToString(selectedState)
            return selectedState, selectedString

    def Qlearning(self, epsilon, gamma, alpha):
        currentState = self.getCurrentStateW()
        #Transformem l'estat en un string
        currentString = self.stateToString(currentState)
        #Guardem l'estat inicial de la taula
        initialState, initialString = currentState, currentString
        self.qTable[currentString] = {}
        #Fixem l'error de les deltes, per veure quan convergeix la Q-table
        error = 0.15
        numIteracions = 0
        numCaminsConvergents = 0

        #Quant tinguem 10 camins seguits, on la Q-table convergeix, pararem el Q-learning.
        while numCaminsConvergents < 10:
            numIteracions += 1
            checkMate = False
            numMovimentsCheckMate = 0
            delta = 0
            while not checkMate:
                #Si no hem visitat l'estat, l'afegim a la Q-table
                if currentString not in self.qTable.keys():
                    self.qTable[currentString] = {}
                listNextStates = []
                #Guardem tots els estats fills en listNextStates
                for state in self.getListNextStatesW(currentState):
                    if state[0][0:2] != [0,4] and state[1][0:2] != [0,4]:
                        listNextStates.append(state)

                #Triem un dels estats mitjançant exploració o explotació.
                nextState, nextString = self.epsilonState(epsilon, listNextStates, currentState)
                qValue = self.qTable[currentString][nextString]
                #Obtenim la recompensa associada a l'estat nextState
                recompensa = self.recompensa(nextState)
                #Si tenim algun escac i mat, el Q-Value ja serà la pròpia recompensa
                #Ja que és un estat terminal.
                if recompensa != -1:
                    qValue = recompensa
                else:
                    #Obtenim el valor de la sample i del Q-value
                    sample = recompensa + gamma*self.maxQValue(nextString, self.qTable)
                    #Anem sumant la diferència entre la recompensa real i la predita.
                    #Si és prou petit, vol dir que estem convergint
                    delta += sample - qValue
                    qValue = (1-alpha)*qValue + alpha*sample

                    numMovimentsCheckMate += 1
                #Actualitzem la taula
                self.qTable[currentString][nextString] = qValue
                if recompensa == -1:
                    #Movem les fitxes a la posició actual
                    self.newBoardSim(nextState+[[0,4,12]])

                    currentState, currentString = nextState, nextString
                #En cas que sigui escac i mat, acabem aquesta iteració del Q-learning.
                else:
                    checkMate = True
            #Calculem la mitjana de la delta
            if numMovimentsCheckMate != 0:
                mitjanaDelta = delta/numMovimentsCheckMate

                #Si està en l'interval (-error, error), vol dir que aquest camí ha convergit.
                if mitjanaDelta < error and mitjanaDelta > -error:
                    numCaminsConvergents += 1
                #Si no, reiniciem el comptador.
                else:
                    numCaminsConvergents = 0
            self.newBoardSim(initialState+[[0,4,12]])
            currentState, currentString = initialState, initialString
            if numIteracions%50 == 0:
                print("Iteració",numIteracions,"amb delta", delta)
        #Quan ja s'acaba l'execució, recuperem el camí que ens porta a una recompensa major.
        self.reconstructPath(initialState)
        print("Hem arribat amb",numIteracions, "iteracions")

    def reconstructPath(self, initialState):
        currentState = initialState
        currentString = self.stateToString(initialState)
        checkMate = False
        self.chess.board.print_board()

        #Afegim l'estat inicial
        path = [initialState]
        while not checkMate:
            currentDict = self.qTable[currentString]
            maxQ = -100000
            maxState = None
            #Mirem quin és el següent estat que té major Q-value
            for stateString in currentDict.keys():
                qValue = currentDict[stateString]
                if maxQ < qValue:
                    maxQ = qValue
                    maxState = stateString
            state = self.stringToState(maxState)
            #Quan l'obtenim l'agefim al path
            path.append(state)
            movement = self.getMovement(currentState,state)
            #Fem el moviment corresponent
            self.chess.move(movement[0],movement[1])
            self.chess.board.print_board()
            currentString = maxState
            currentState = state
            #Quan ja s'aconsegueix fer check mate, s'acaba l'execució.
            if self.isCheckMate(state):
                checkMate = True

        print("Seqüència de moviments: ",path)

    def explorationFunction(self, listStates, currentState, torn):
        #Funció d'exploració per l'exercici 2.
        #Al final no la fem servir
        currentString = self.BWStateToString(currentState)
        #Si és el torn de les blanques
        if torn:
            currentDict = self.qTableWhites[currentString]
            numVisitedTable = self.numVisitedWhites[currentString]
        # Si és el torn de les negres
        else:
            currentDict = self.qTableBlacks[currentString]
            numVisitedTable = self.numVisitedBlacks[currentString]

        #Fixem una K. Fem una estimació del q-Value que podem arribar a tenir.
        k = self.kValue
        maxValue = float('-inf')
        listVisitedStates = currentDict.keys()
        #Fixem un marge per agafar els estats màxims.
        error = self.errorValue
        listBestStates = []

        for state in listStates:
            stringState = self.BWStateToString(state)
            if stringState not in listVisitedStates:
                currentDict[stringState] = 0
                numVisitedTable[stringState] = 0

            qValue = currentDict[stringState]
            #Agafem el nombre de vegades que hem visitat l'estat
            N = numVisitedTable[stringState]
            #Si no l'hem visitat, automàticament el visitem.
            if N == 0:
                return state, stringState

            #Fem una estimació del valor que podria arribar a tenir aquest estat, considerant el número
            #de vegades visitat
            estimatedValue = qValue + k/N

            if estimatedValue > maxValue:
                maxValue = estimatedValue

        #En aquesta iteració agafarem tots els estat que estiguin dins del marge de l'error
        for state in listStates:
            stringState = self.BWStateToString(state)
            qValue = currentDict[stringState]
            N = numVisitedTable[stringState]
            estimatedValue = qValue + k/N
            if estimatedValue >= maxValue - error and estimatedValue <= maxValue + error:
                listBestStates.append((state, stringState))

        #Agafem un estat arbritrari dins dels considerats.
        n = random.randint(0,len(listBestStates)-1)
        maxState, maxStateString = listBestStates[n][0], listBestStates[n][1]
        return maxState, maxStateString

    def epsilonStateBW(self, epsilon, listStates, currentState, torn):
        x = random.uniform(0,1)
        currentString = self.BWStateToString(currentState)

        if torn:
            currentDict = self.qTableWhites[currentString]
            numVisitedTable = self.numVisitedWhites[currentString]
        else:
            currentDict = self.qTableBlacks[currentString]
            numVisitedTable = self.numVisitedBlacks[currentString]

        visitedStatesString = currentDict.keys()

        #Fem exploració amb probabilitat epsilon
        if x < epsilon:
            n = random.randint(0, len(listStates) - 1)
            randomState = listStates[n]
            randomStateString = self.BWStateToString(randomState)
            if randomStateString not in visitedStatesString:
                currentDict[randomStateString] = 0
                numVisitedTable[randomStateString] = 0
            return randomState, randomStateString

        #Fem exploració amb probabilitat 1 - epsilon
        else:
            listBestStates = []
            maxValue = float('-inf')
            error = 0.5
            #Un primer bucle per trobar el màxim valor
            for state in listStates:
                stateString = self.BWStateToString(state)
                #Si l'estat no ha estat visitat, l'inicialitzem
                if stateString not in visitedStatesString:
                    currentDict[stateString] = 0
                    numVisitedTable[stateString] = 0
                qValue = currentDict[stateString]

                if qValue > maxValue:
                    maxValue = qValue
            #Un segnon bucle per trobar els millors estats
            minFrequency = float('inf')
            indexMinFrequency = 0
            for state in listStates:
                stateString = self.BWStateToString(state)
                qValue = currentDict[stateString]
                #Valorem si el valor es troba dins d'un marge d'error del major valor trobat
                #En cas afirmatiu, l'afegim als millors estats possibles
                if qValue <= maxValue + error and qValue >= maxValue - error:
                    if numVisitedTable[stateString] < minFrequency:
                        selectedState = state
                        selectedString = stateString
                        minFrequency = numVisitedTable[stateString]

            return selectedState, selectedString
        return

    def reconstructPathBW(self, initialState):
        currentState = initialState
        currentString = self.BWStateToString(initialState)
        checkMate = False

        #Afegim l'estat inicial
        path = [initialState]
        torn = False
        while not checkMate:
            self.newBoardSim(currentState)
            self.chess.board.print_board()
            torn = not torn
            #Agafem els estats següents
            nextStates = self.getCompleteNextStates(torn, currentState)
            if torn:
                currentDict = self.qTableWhites[currentString]
            else:
                currentDict = self.qTableBlacks[currentString]

            maxQ = -100000
            maxState = None
            maxString = None

            #Mirem quin és el següent estat que té major Q-value
            for state in nextStates:
                stateString = self.BWStateToString(state)

                qValue = currentDict[stateString]
                if maxQ < qValue:
                    maxQ = qValue
                    maxState = state
                    maxString = stateString


            #Quan l'obtenim l'afegim al path
            path.append(maxState)
            movement = self.getMovement(currentState,maxState)
            #Fem el moviment corresponent
            self.chess.move(movement[0],movement[1])

            currentString = maxString
            currentState = maxState
            #Quan ja s'aconsegueix fer check mate, s'acaba l'execució.
            if torn and self.isBlackInCheckMate(maxState):
                checkMate = True
            if not torn and self.isWhiteInCheckMate(maxState):
                checkMate = True

        self.newBoardSim(currentState)
        self.chess.board.print_board()
        print(path)

    def recompensaBW(self, currentState, torn, previousState):
        previousBrState = self.getPieceState(previousState, 8)
        brState = self.getPieceState(currentState, 8)
        wrState = self.getPieceState(currentState, 2)

        if self.allBkMovementsWatched(currentState) and torn:
            #Si el rei negre està en check mate
            if self.isWatchedBk(currentState):
                #Retornem recompensa i com que és un estat terminal, True.
                return 5000, True
            #Estem en empat
            else:
                #Retornem recompensa i com que és un estat terminal, True.
                return 0, True

        if self.allWkMovementsWatched(currentState) and not torn:
            # Si el rei blanc està en check mate
            if self.isWatchedWk(currentState):
                # Retornem recompensa i com que és un estat terminal, True.
                return 5000, True
            # Estem en empat
            else:
                # Retornem recompensa i com que és un estat terminal, True.
                return 0, True
        #Les dues torres estan vives
        if brState != None and wrState != None:
            #No ens interessen les dues torres vives.
            #Per tant, el cost per sobreviure és major per les blanques
            if torn:
                return -2, False
            else:
                return 2, False
        #Les dues torres estan mortes
        if brState == None and wrState == None:
            #Rei negre ha matat a la torre blanca. S'acaba la partida i compta com "mini-victòria" per les negres.
            return 400, True
        if brState == None:
            #Si les blanques just han matat la torre negra, és torn de les blanques, recompensa positiva
            if previousBrState != None:
                return 100, False
            #Si la torre negra ja està morta, a les blanques ara els costa menys sobreviure.
            if torn:
                return -0.5, False
            #Ens interessa que les negres intentin sobreviure el màxim possible,
            # per tant sobreviure té un valor positiu.
            else:
                return 0.5, False
        if wrState == None:
            #Les negres han matat la torre blanca. Per tant, és torn de les negres i 'mini-victòria' per les negres
            return 400, True
        return

    def getCompleteNextStates(self, color, currentState):
        listNextStates = []
        #Si són les blanques
        if color:
            blackState = self.getBlackState(currentState)
            brState = self.getPieceState(currentState, 8)
            # Guardem tots els estats fills en listNextStates
            for state in self.getListNextStatesW(self.getWhiteState(currentState)):
                newBlackState = blackState.copy()
                # Comprovem si s'han menjat la torre negra. En cas afirmatiu, treiem l'estat de la torre negra
                if brState != None and brState[0:2] == state[0][0:2]:
                    newBlackState.remove(brState)
                # Ara, state, serà el nostre estat actual
                state = state + newBlackState
                if not self.isWatchedWk(state):
                    listNextStates.append(state)
        else:
            whiteState = self.getWhiteState(currentState)
            wrState = self.getPieceState(currentState, 2)
            # Guardem tots els estats fills en listNextStates
            for state in self.getListNextStatesB(self.getBlackState(currentState)):
                newWhiteState = whiteState.copy()
                # Comprovem si s'han menjat la torre blanca. En cas afirmatiu, treiem l'estat de la torre blanca
                if wrState != None and wrState[0:2] == state[0][0:2]:
                    newWhiteState.remove(wrState)
                # Ara, state, serà el nostre estat actual
                state = state + newWhiteState
                if not self.isWatchedBk(state):
                    listNextStates.append(state)

        return listNextStates

    def towersAlive(self, currentState):
        return self.getPieceState(currentState,2) != None and self.getPieceState(currentState,8) != None

    def propagation2(self, listMovements, listMovementsStrings, alpha, gamma, torn):
        #Utilitzem el mètode per propagar els valors d'un estat final en tot el camí recorregut.
        #Això es fa quan les blanques fan un check mate o el rei negre mata a la torre blanca
        numMoves = len(listMovementsStrings)
        rangePropagation = numMoves - 1
        #Anem propagant els Q-values de tots els estats del camí seguit.
        #Per fer-ho, comencem per l'últim estat abans de fer check mate, i actualitzem el seu Q-value
        #Després considerem l'estat d'abans d'aquest i aquest mateix, i actualitzem els seus Q-values.
        #Es fa això successivament, fins arribar a actualitzar des del primer moviment, fins l'últim.
        for j in range(1, rangePropagation):
            tornPropagation = not torn
            for i in range(1, j+1):
                prevMoveString = listMovementsStrings[numMoves - 2 - i]
                nextMoveString = listMovementsStrings[numMoves - 1 - i]
                prevMove = listMovements[numMoves - 2 - i]
                nextMove = listMovements[numMoves - 1 - i]
                if tornPropagation:
                    qValue = self.qTableWhites[prevMoveString][nextMoveString]
                    recompensaP, isFinalStateP = self.recompensaBW(nextMove, tornPropagation, prevMove)
                    sample = recompensaP - gamma * self.maxQValue(nextMoveString, self.qTableBlacks)
                    qValue = (1 - alpha) * qValue + alpha * sample
                    self.qTableWhites[prevMoveString][nextMoveString] = qValue
                    self.numVisitedWhites[prevMoveString][nextMoveString] += 1
                else:
                    qValue = self.qTableBlacks[prevMoveString][nextMoveString]
                    recompensaP, isFinalStateP = self.recompensaBW(nextMove, tornPropagation, prevMove)
                    sample = recompensaP - gamma * self.maxQValue(nextMoveString, self.qTableWhites)
                    qValue = (1 - alpha) * qValue + alpha * sample
                    self.qTableBlacks[prevMoveString][nextMoveString] = qValue
                    self.numVisitedBlacks[prevMoveString][nextMoveString] += 1
                tornPropagation = not tornPropagation
        return

    def propagationUnaVegada(self, listMovements, listMovementsStrings, alpha, gamma, tornPropagation):
        # Utilitzem el mètode per propagar els valors d'un estat final en tot el camí recorregut.
        # Això es fa quan les blanques fan un check mate o el rei negre mata a la torre blanca
        numMoves = len(listMovementsStrings)
        recompensaAcumulada = 0
        tornPropagation = not tornPropagation
        #Fem propagació una sola vegada per tot el camí. Començant pel penúltim estat fins el primer de tots.
        for j in range(numMoves - 2, 0, -1):
            prevMoveString = listMovementsStrings[j - 1]
            nextMoveString = listMovementsStrings[j]
            prevMove = listMovements[j - 1]
            nextMove = listMovements[j]

            if tornPropagation:
                currentDict = self.qTableWhites[prevMoveString]
                numVisitedTable = self.numVisitedWhites[prevMoveString]
                rivalDict = self.qTableBlacks

            # Si és el torn de les negres
            else:
                currentDict = self.qTableBlacks[prevMoveString]
                numVisitedTable = self.numVisitedBlacks[prevMoveString]
                rivalDict = self.qTableWhites


            qValue = currentDict[nextMoveString]
            recompensaP, isFinalStateP = self.recompensaBW(nextMove, tornPropagation, prevMove)
            sample = recompensaP + gamma * (-1) * self.maxQValue(nextMoveString, rivalDict)
            qValue = (1 - alpha) * qValue + alpha * sample

            currentDict[nextMoveString] = qValue
            numVisitedTable[nextMoveString] += 1

            tornPropagation = not tornPropagation

        return

    def propagation(self, listMovements, listMovementsStrings, alpha, gamma, tornPropagation):
        # Utilitzem el mètode per propagar els valors d'un estat final en tot el camí recorregut.
        # Això es fa quan les blanques fan un check mate o el rei negre mata a la torre blanca
        numMoves = len(listMovementsStrings)
        recompensaAcumulada = 0
        #Fem propagació una sola vegada per tot el camí. Començant pel penúltim estat fins el primer de tots.
        for j in range(numMoves - 1, 0, -1):
            prevMoveString = listMovementsStrings[j - 1]
            nextMoveString = listMovementsStrings[j]
            prevMove = listMovements[j - 1]
            nextMove = listMovements[j]

            if tornPropagation:
                currentDict = self.qTableWhites[prevMoveString]
                numVisitedTable = self.numVisitedWhites[prevMoveString]
                rivalDict = self.qTableBlacks

            # Si és el torn de les negres
            else:
                currentDict = self.qTableBlacks[prevMoveString]
                numVisitedTable = self.numVisitedBlacks[prevMoveString]
                rivalDict = self.qTableWhites


            qValue = currentDict[nextMoveString]
            recompensaP, isFinalStateP = self.recompensaBW(nextMove, tornPropagation, prevMove)

            recompensaAcumulada = recompensaP - gamma * (recompensaAcumulada)

            if j != numMoves -1:
                sample = recompensaAcumulada + gamma * (-1) * self.maxQValue(nextMoveString, rivalDict)
                qValue = (1 - alpha) * qValue + alpha * sample

                currentDict[nextMoveString] = qValue
                numVisitedTable[nextMoveString] += 1

            tornPropagation = not tornPropagation

        return

    def QlearningWhitesVsBlacksExplorationFunction(self, alpha, gamma):
        #Aquest algorisme utilitza la funció d'exploració
        #Després de diverses proves hem vist que no troba la solució òptima.
        torn = True

        initialState = self.getCurrentState()
        initialString = self.BWStateToString(initialState)
        currentState = initialState
        currentString = initialString
        #Restringim el número de moviments per cada partida.
        numMaxMoviments = 20
        numMaxMovimentsTowerDead = 80

        error = 0.15
        numIteracions = 0
        numCaminsConvergents = 0
        numCheckMates = 0
        numIteracionsUltimate = 0

        indexList = 0
        listCheckMates = self.checkMateList()
        checkMateExploration = True
        listMiddleStates = self.middleStatesList()
        middleExploration = False

        loadQTable = True
        if loadQTable:
            checkMateExploration = False
            middleExploration = True
            self.loadQTable()
            numIteracions = 15500
            indexList = 3

        #Només sortirem quan tinguem suficients camins convergents i estem a la configuració final.
        while numCaminsConvergents < 10 or checkMateExploration or middleExploration:
            numIteracions += 1
            finalState = False
            numMovimentsBlanques = 0
            numMovimentsNegres = 0
            deltaBlanques = 0
            deltaNegres = 0
            comptMoviments = 0

            if checkMateExploration:
                numMaxMovimentsTowerDead = 25
                if indexList == len(listCheckMates) - 1 and numCheckMates == 3:
                    checkMateExploration = False
                    middleExploration = True
                    self.saveQTable()
                    numCaminsConvergents = 0
                    indexList = 0
                else:
                    if numCheckMates == 3:
                        indexList +=1
                        numCheckMates = 0
                        print("\n")
                        print("CHECKMATE INDEX",indexList)
                        print("\n")
                    currentState = listCheckMates[indexList]
                    currentString = self.BWStateToString(currentState)
                    self.newBoardSim(currentState)

            if middleExploration:
                numMaxMovimentsTowerDead = 60
                if indexList == len(listMiddleStates) - 1 and numCaminsConvergents >= 10:
                    numCaminsConvergents = 0
                    middleExploration = False

                    self.saveQTable()
                else:
                    if numCaminsConvergents >= 10:
                        indexList += 1
                        numCaminsConvergents = 0
                        print("\n")
                        print("MIDDLE INDEX", indexList)
                        print("\n")
                        self.saveQTable()
                    currentState = listMiddleStates[indexList][0]
                    numMaxMovimentsTowerDead = listMiddleStates[indexList][1]
                    currentString = self.BWStateToString(currentState)
                    self.newBoardSim(currentState)
                if numIteracions%500 == 0:
                    self.saveQTable()

            if not middleExploration and not checkMateExploration:
                numMaxMovimentsTowerDead = 70
                self.newBoardSim(initialState)
                currentState, currentString = initialState, initialString
                numIteracionsUltimate += 1

                if numIteracionsUltimate > 35:
                    print(self.qTableWhites[currentString])
                    if '03x736072008' in self.qTableWhites[currentString].keys():
                        print(self.qTableWhites[currentString]['03x736072008'])
                        print(self.qTableBlacks['03x736072008'])
                if numIteracions%500 == 0:
                    self.saveQTable()

            torn = True

            listMovements = [currentState]
            listMovementsStrings = [currentString]

            while not finalState:
                if (comptMoviments >= numMaxMoviments and self.towersAlive(currentState)) or comptMoviments >= numMaxMovimentsTowerDead:
                    break
                if torn:
                    # Si no hem visitat l'estat, l'afegim a la q-table
                    if currentString not in self.qTableWhites.keys():
                        self.qTableWhites[currentString] = {}
                        self.numVisitedWhites[currentString] = {}

                    listNextStates = self.getCompleteNextStates(torn, currentState)

                    # Triem un dels estats mitjançant exploració o explotació.
                    nextState, nextString = self.explorationFunction(listNextStates, currentState, torn)
                    listMovementsStrings.append(nextString)
                    listMovements.append(nextState)

                    qValue = self.qTableWhites[currentString][nextString]
                    self.numVisitedWhites[currentString][nextString]+=1

                    # Obtenim la recompensa associada a l'estat nextState, i si és un estat terminal
                    recompensa, isFinalState = self.recompensaBW(nextState, torn, currentState)

                    # Si tenim algun escac i mat, el Q-Value ja serà la pròpia recompensa
                    # Ja que és un estat terminal.
                    if isFinalState:
                        qValue = recompensa
                    else:
                        # Obtenim el valor de la sample i del Q-value
                        sample = recompensa + gamma * (-1) * self.maxQValue(nextString, self.qTableBlacks)
                        deltaBlanques += sample - qValue
                        qValue = (1 - alpha) * qValue + alpha * sample
                    # Actualitzem la taula
                    self.qTableWhites[currentString][nextString] = qValue
                    if not isFinalState:
                        # Movem les fitxes a la posició actual
                        self.newBoardSim(nextState)

                        currentState, currentString = nextState, nextString
                        numMovimentsBlanques += 1
                    # En cas que sigui escac i mat, acabem aquesta iteració del Q-learning.
                    else:
                        # Movem les fitxes a la posició actual
                        ############
                        self.newBoardSim(nextState)
                        ###########
                        #Si s'ha produit checkmate, propaguem valor.
                        if self.isWatchedBk(nextState):
                            #Comptem els número de checkMates que s'han fet seguits.
                            numCheckMates +=1
                            print("\n\nCHECKMATE\n\n")
                            self.propagation(listMovements, listMovementsStrings, alpha, gamma, torn)
                            ###########
                            self.newBoardSim(nextState)
                            ###########

                        finalState = True

                else:
                    # Si no hem visitat l'estat, l'afegim a la q-table
                    if currentString not in self.qTableBlacks.keys():
                        self.qTableBlacks[currentString] = {}
                        self.numVisitedBlacks[currentString] = {}

                    listNextStates = self.getCompleteNextStates(torn, currentState)


                    # Triem un dels estats mitjançant exploració o explotació.
                    nextState, nextString = self.explorationFunction(listNextStates, currentState, torn)


                    listMovementsStrings.append(nextString)
                    listMovements.append(nextState)


                    qValue = self.qTableBlacks[currentString][nextString]
                    self.numVisitedBlacks[currentString][nextString]+=1

                    # Obtenim la recompensa associada a l'estat nextState i si és un estat terminal.
                    recompensa, isFinalState = self.recompensaBW(nextState, torn, currentState)

                    # Si tenim algun escac i mat, el Q-Value ja serà la pròpia recompensa
                    # Ja que és un estat terminal.
                    if isFinalState:
                        qValue = recompensa
                    else:
                        # Obtenim el valor de la sample i del Q-value
                        sample = recompensa + gamma * (-1) * self.maxQValue(nextString, self.qTableWhites)
                        deltaNegres += sample - qValue
                        qValue = (1 - alpha) * qValue + alpha * sample
                    # Actualitzem la taula
                    self.qTableBlacks[currentString][nextString] = qValue
                    if not isFinalState:
                        # Movem les fitxes a la posició actual
                        self.newBoardSim(nextState)

                        currentState, currentString = nextState, nextString
                        numMovimentsNegres += 1
                    #Les negres han matat la torre blanca.
                    else:
                        self.propagation(listMovements, listMovementsStrings, alpha, gamma, torn)
                        ##########
                        self.newBoardSim(nextState)
                        ##########
                        finalState = True

                torn = not torn
                comptMoviments += 1

            # Calculem la mitjana de la delta
            if numMovimentsBlanques != 0 and numMovimentsNegres != 0:
                mitjanaDeltaBlanques = deltaBlanques / numMovimentsBlanques
                mitjanaDeltaNegres = deltaNegres / numMovimentsNegres
                print(numIteracions, mitjanaDeltaBlanques, mitjanaDeltaNegres)
                # Si està en l'interval (-error, error), vol dir que aquest camí ha convergit.
                if mitjanaDeltaBlanques < error and mitjanaDeltaBlanques > -error and mitjanaDeltaNegres < error and mitjanaDeltaNegres > -error:
                    numCaminsConvergents += 1
                # Si no, reiniciem el comptador.
                else:
                    numCaminsConvergents = 0




        self.reconstructPathBW(initialState)
        return 0

    def QlearningWhitesVsBlacksEpsilon(self, alpha, gamma, epsilon):
        torn = True

        initialState = self.getCurrentState()
        initialString = self.BWStateToString(initialState)
        currentState = initialState
        currentString = initialString
        # Restringim el número de moviments per cada partida.
        numMaxMoviments = 20
        numMaxMovimentsTowerDead = 80

        error = 0.15
        numIteracions = 0
        numCaminsConvergents = 0
        numCheckMates = 0
        numIteracionsUltimate = 0

        indexList = 0
        listCheckMates = self.checkMateList()
        checkMateExploration = True
        listMiddleStates = self.middleStatesList()
        middleExploration = False
        """
        Per fer aquesta execució, hem anat guardant la Q-table de les blanques i negres a un fitxer,
        juntament amb la taula amb el número d'accions visitades tant per les blanques com per les negres.
        Per tal de recuperar els resultat de les Q-tables, podem fer load del fitxer on els hem guardats.
        Per recuperar el procés de l'execució cal indicar si encara s'estan executant els middle states, i
        en aquest cas posar l'índex del middle state pel qual va; en cas que ja estigui executant 
        el problema final, cal posar el middleExploration en False.
        Per qualsevol de les dues opcions, si es vol tenir constància del nombre d'iteracions que porta, 
        s'ha de posar a numIteracions
        """
        loadQTable = False
        if loadQTable:
            checkMateExploration = False
            middleExploration = True
            self.loadQTable()
            #numIteracions = 28000
            #indexList = 2

        # Només sortirem quan tinguem suficients camins convergents i estem a la configuració final.
        while numCaminsConvergents < 10 or checkMateExploration or middleExploration:
            numIteracions += 1
            #Booleà per indicar si ja s'ha acabat la partida.
            finalState = False
            numMovimentsBlanques = 0
            numMovimentsNegres = 0
            deltaBlanques = 0
            deltaNegres = 0
            comptMoviments = 0

            if checkMateExploration:
                numMaxMovimentsTowerDead = 25
                #Ja s'ha executat l'últim check mate state
                if indexList == len(listCheckMates) - 1 and numCheckMates == 3:
                    checkMateExploration = False
                    middleExploration = True
                    #Guardem les taules en un fitxer.
                    self.saveQTable()
                    numCaminsConvergents = 0
                    indexList = 0
                else:
                    #S'hi ja s'han fet 3 checkmates, considerem que ja ha après suficient aquest checkmate
                    #
                    if numCheckMates == 3:
                        indexList += 1
                        numCheckMates = 0
                        print("CHECKMATE INDEX", indexList,". Ha arribat en", numIteracions, "iteracions.")
                    currentState = listCheckMates[indexList]
                    currentString = self.BWStateToString(currentState)
                    self.newBoardSim(currentState)

            if middleExploration:
                #Ja ha executat l'últim middle state, i les taules han convergit. Passem a executar el problema final.
                if indexList == len(listMiddleStates) - 1 and numCaminsConvergents >= 10:
                    numCaminsConvergents = 0
                    middleExploration = False
                    print("Executem la configuració final!")
                    #Guardem les taules
                    self.saveQTable()
                else:
                    if numCaminsConvergents >= 10:
                        indexList += 1
                        numCaminsConvergents = 0
                        print("MIDDLE INDEX", indexList, ". Ha arribat en", numIteracions, "iteracions.")
                        self.saveQTable()
                    currentState = listMiddleStates[indexList][0]
                    numMaxMovimentsTowerDead = listMiddleStates[indexList][1]
                    currentString = self.BWStateToString(currentState)
                    self.newBoardSim(currentState)
                #Cada 500 iteracions guardem el procés.
                if numIteracions % 500 == 0:
                    self.saveQTable()

            if not middleExploration and not checkMateExploration:
                numMaxMovimentsTowerDead = 70
                self.newBoardSim(initialState)
                currentState, currentString = initialState, initialString
                numIteracionsUltimate += 1
                if numIteracions % 500 == 0:
                    self.saveQTable()

            torn = True
            #Anem guardant tots els moviments que fem per si després hem de er propagació
            listMovements = [currentState]
            listMovementsStrings = [currentString]

            while not finalState:
                #Si hem arribat al màxim de moviements permesos, acabem aquesta partida
                if (comptMoviments >= numMaxMoviments and self.towersAlive(
                        currentState)) or comptMoviments >= numMaxMovimentsTowerDead:
                    break
                if torn:
                    # Si no hem visitat l'estat, l'afegim a la q-table
                    if currentString not in self.qTableWhites.keys():
                        self.qTableWhites[currentString] = {}
                        self.numVisitedWhites[currentString] = {}

                    listNextStates = self.getCompleteNextStates(torn, currentState)

                    # Triem un dels estats mitjançant exploració o explotació.
                    nextState, nextString = self.epsilonStateBW(epsilon, listNextStates, currentState, torn)
                    listMovementsStrings.append(nextString)
                    listMovements.append(nextState)

                    qValue = self.qTableWhites[currentString][nextString]
                    self.numVisitedWhites[currentString][nextString] += 1

                    # Obtenim la recompensa associada a l'estat nextState, i si és un estat terminal
                    recompensa, isFinalState = self.recompensaBW(nextState, torn, currentState)

                    # Si tenim algun escac i mat, el Q-Value ja serà la pròpia recompensa, ja que és un estat terminal.
                    if isFinalState:
                        qValue = recompensa
                    else:
                        # Obtenim el valor de la sample i del Q-value
                        sample = recompensa + gamma * (-1) * self.maxQValue(nextString, self.qTableBlacks)
                        #Anem calculant la delta de les blanques per veure si el camí és convergent.
                        deltaBlanques += sample - qValue
                        qValue = (1 - alpha) * qValue + alpha * sample
                    # Actualitzem la taula
                    self.qTableWhites[currentString][nextString] = qValue
                    if not isFinalState:
                        # Movem les fitxes a la posició actual
                        self.newBoardSim(nextState)

                        currentState, currentString = nextState, nextString
                        numMovimentsBlanques += 1
                    # En cas que sigui escac i mat o un empat, acabem aquesta iteració del Q-learning.
                    else:
                        # Si s'ha produit checkmate, propaguem valor.
                        if self.isWatchedBk(nextState):
                            # Comptem els número de checkMates que s'han fet seguits.
                            numCheckMates += 1
                            self.propagation(listMovements, listMovementsStrings, alpha, gamma, torn)
                        #Indiquem que s'acaba la partida
                        finalState = True
                #Ara és el torn de les negres
                else:
                    # Si no hem visitat l'estat, l'afegim a la q-table
                    if currentString not in self.qTableBlacks.keys():
                        self.qTableBlacks[currentString] = {}
                        self.numVisitedBlacks[currentString] = {}

                    listNextStates = self.getCompleteNextStates(torn, currentState)

                    # Triem un dels estats mitjançant exploració o explotació.
                    nextState, nextString = self.epsilonStateBW(epsilon, listNextStates, currentState, torn)

                    listMovementsStrings.append(nextString)
                    listMovements.append(nextState)

                    qValue = self.qTableBlacks[currentString][nextString]
                    self.numVisitedBlacks[currentString][nextString] += 1

                    # Obtenim la recompensa associada a l'estat nextState i si és un estat terminal.
                    recompensa, isFinalState = self.recompensaBW(nextState, torn, currentState)

                    # Si tenim algun escac i mat, el Q-Value ja serà la pròpia recompensa, ja que és un estat terminal.
                    if isFinalState:
                        qValue = recompensa
                    else:
                        # Obtenim el valor de la sample i del Q-value
                        sample = recompensa + gamma * (-1) * self.maxQValue(nextString, self.qTableWhites)
                        deltaNegres += sample - qValue
                        qValue = (1 - alpha) * qValue + alpha * sample
                    # Actualitzem la taula
                    self.qTableBlacks[currentString][nextString] = qValue

                    if not isFinalState:
                        # Movem les fitxes a la posició actual
                        self.newBoardSim(nextState)

                        currentState, currentString = nextState, nextString
                        numMovimentsNegres += 1
                    # Les negres han matat la torre blanca.
                    else:
                        #Fem propagació del valor i indiquem que s'ha acabat la partida
                        self.propagation(listMovements, listMovementsStrings, alpha, gamma, torn)
                        finalState = True

                torn = not torn
                comptMoviments += 1

            # Calculem la mitjana de les deltes per veure si el camí ha convergit
            if numMovimentsBlanques != 0 and numMovimentsNegres != 0:
                mitjanaDeltaBlanques = deltaBlanques / numMovimentsBlanques
                mitjanaDeltaNegres = deltaNegres / numMovimentsNegres
                if numIteracions%10 == 0:
                    print("Iteració", numIteracions, " amb delta blanques ",mitjanaDeltaBlanques, "i delta negres",mitjanaDeltaNegres)
                # Si està en l'interval (-error, error), vol dir que aquest camí ha convergit.
                if mitjanaDeltaBlanques < error and mitjanaDeltaBlanques > -error and mitjanaDeltaNegres < error and mitjanaDeltaNegres > -error:
                    numCaminsConvergents += 1
                # Si no, reiniciem el comptador.
                else:
                    numCaminsConvergents = 0
        #Quan acabem el problema, mirem quin és el millor recorregut
        self.reconstructPathBW(initialState)
        return 0

    def loadQTable(self):
        #Recuperem els fitxers i guardem l'informació en les taules utilitzades.
        kValueEValue = 'K'+str(self.kValue) +'E'+ str(self.errorValue)
        with open('qTableWhites'+kValueEValue+'.txt') as fW:
            dataW = fW.read()
        self.qTableWhites = json.loads(dataW)

        with open('numVisitedWhites'+kValueEValue+'.txt') as fNW:
            dataNW = fNW.read()
        self.numVisitedWhites = json.loads(dataNW)

        with open('qTableBlacks'+kValueEValue+'.txt') as fB:
            dataB = fB.read()
        self.qTableBlacks = json.loads(dataB)

        with open('numVisitedBlacks'+kValueEValue+'.txt') as fNB:
            dataNB = fNB.read()
        self.numVisitedBlacks = json.loads(dataNB)
        return

    def saveQTable(self):
        #Guardem el procés de les taules en els fitxers.
        #Si ja existeixen, primer de tot, s'eliminen els ja existents i en creem de nous.
        kValueEValue = 'K'+str(self.kValue) +'E'+ str(self.errorValue)
        if os.path.exists("qTableWhites"+kValueEValue+".txt"):
            os.remove("qTableWhites"+kValueEValue+".txt")
        with open('qTableWhites'+kValueEValue+'.txt', 'w') as data:
            data.write(json.dumps(self.qTableWhites))

        if os.path.exists("numVisitedWhites"+kValueEValue+".txt"):
            os.remove("numVisitedWhites"+kValueEValue+".txt")
        with open('numVisitedWhites'+kValueEValue+'.txt', 'w') as data:
            data.write(json.dumps(self.numVisitedWhites))

        if os.path.exists("qTableBlacks"+kValueEValue+".txt"):
            os.remove("qTableBlacks"+kValueEValue+".txt")
        with open('qTableBlacks'+kValueEValue+'.txt', 'w') as data:
            data.write(json.dumps(self.qTableBlacks))

        if os.path.exists("numVisitedBlacks"+kValueEValue+".txt"):
            os.remove("numVisitedBlacks"+kValueEValue+".txt")
        with open('numVisitedBlacks'+kValueEValue+'.txt', 'w') as data:
            data.write(json.dumps(self.numVisitedBlacks))

        return



def translate(s):
    """
    Translates traditional board coordinates of chess into list indices
    """

    try:
        row = int(s[0])
        col = s[1]
        if row < 1 or row > 8:
            print(s[0] + "is not in the range from 1 - 8")
            return None
        if col < 'a' or col > 'h':
            print(s[1] + "is not in the range from a - h")
            return None
        dict = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        return (8 - row, dict[col])
    except:
        print(s + "is not in the format '[number][letter]'")
        return None


if __name__ == "__main__":
    #   if len(sys.argv) < 2:
    #       sys.exit(usage())

    # intiialize board
    TA = np.zeros((8, 8))

    #Configuració inicial del taulell
    TA[7][0] = 2
    TA[7][4] = 6
    TA[0][7] = 8
    TA[0][4] = 12


    # initialise board
    print("stating AI chess... ")
    aichess = Aichess(TA, True)
    numExercici = 2

    if numExercici == 1:
        aichess.Qlearning(0.3, 0.9, 0.1)

    if numExercici == 2:
        aichess.QlearningWhitesVsBlacksEpsilon(0.1, 0.9, 0.3)
