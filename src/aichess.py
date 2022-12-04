#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 11:22:03 2022

@author: ignasi
"""
import copy
import math

import chess
import board
import numpy as np
import sys
import queue
from typing import List
import random

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
        self.listVisitedStates = []
        self.listVisitedSituations = []
        self.pathToTarget = []
        self.currentStateW = self.chess.boardSim.currentStateW;
        self.depthMax = 8;
        self.checkMate = False
        self.qTable = {}
        self.qTableWhites = {}
        self.qTableBlacks = {}


    def stateToString(self, whiteState):
        stringState = ""
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

    def BWStateToString(self, state):
        stringState = ""
        wrState = self.getPieceState(state,2)
        if wrState != None:
            stringState += str(wrState[0])+str(wrState[1])+str(2)
        wkState = self.getPieceState(state, 6)
        stringState += str(wkState[0]) + str(wkState[1]) + str(6)

        brState = self.getPieceState(state, 8)
        if brState != None:
            stringState += str(brState[0]) + str(brState[1]) + str(8)
        bkState = self.getPieceState(state, 12)
        stringState += str(bkState[0]) + str(bkState[1]) + "x"
        return stringState

    def stringToBWState(self, string):
        state = []
        for i in range(0,len(string),3):
            numPiece = string[i+2]
            if numPiece == "x":
                numPiece = 12
            else: numPiece = int(numPiece)
            state.append([int(string[i]), int(string[i+1]), numPiece])
        return state

    def copyState(self, state):
        copyState = []
        for piece in state:
            copyState.append(piece.copy())
        return copyState
    def isVisitedSituation(self, color, mystate):
        if (len(self.listVisitedSituations) > 0):
            perm_state = list(permutations(mystate))

            isVisited = False
            for j in range(len(perm_state)):

                for k in range(len(self.listVisitedSituations)):
                    if self.isSameState(list(perm_state[j]), self.listVisitedSituations.__getitem__(k)[1]) and color == \
                            self.listVisitedSituations.__getitem__(k)[0]:
                        isVisited = True

            return isVisited
        else:
            return False


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

    def isSameState(self, a, b):

        isSameState1 = True
        # a and b are lists
        for k in range(len(a)):

            if a[k] not in b:
                isSameState1 = False

        isSameState2 = True
        # a and b are lists
        for k in range(len(b)):

            if b[k] not in a:
                isSameState2 = False

        isSameState = isSameState1 and isSameState2
        return isSameState

    def isVisited(self, mystate):

        if (len(self.listVisitedStates) > 0):
            perm_state = list(permutations(mystate))

            isVisited = False
            for j in range(len(perm_state)):

                for k in range(len(self.listVisitedStates)):

                    if self.isSameState(list(perm_state[j]), self.listVisitedStates[k]):
                        isVisited = True

            return isVisited
        else:
            return False

    def isWatchedBk(self, currentState):
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
        #posem els possibles estats on es produeixi check mate
        listCheckMateStates = [[[0,0,2],[2,4,6]],[[0,1,2],[2,4,6]],[[0,2,2],[2,4,6]],[[0,6,2],[2,4,6]],[[0,7,2],[2,4,6]]]

        #Mirem totes les permutacions de l'estat i si coincideixen amb la llista de CheckMates
        for permState in list(permutations(mystate)):
            if list(permState) in listCheckMateStates:
                return True

        return False

    def recompensa(self, mystate):
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
        #Fem exploració amb probabilitat 1 - epsilon
        else:
            listBestStates = []
            maxValue = -10000
            currentDict = self.qTable[self.stateToString(currentState)]
            visitedStatesString = currentDict.keys()
            error = 0.01
            for state in listStates:
                stateString = self.stateToString(state)
                #Si l'estat no ha estat visitat, l'inicialitzem
                if stateString not in visitedStatesString:
                    currentDict[stateString] = 0
                qValue = currentDict[stateString]
                #Valorem si el valor es troba dins d'un marge d'error del major valor trobat
                #En cas afirmatiu, l'afegim als millors estats possibles
                if qValue <= maxValue + error and qValue >= maxValue - error:
                    listBestStates.append(state)
                #Si el valor está fora de rang i és major que el major valor trobat, passa a ser el valor
                #màxim.
                elif qValue > maxValue:
                    maxValue = qValue
                    listBestStates.clear()
                    listBestStates.append(state)

            n = random.randint(0, len(listBestStates) - 1)
            nextState = listBestStates[n]
            nextString = self.stateToString(nextState)
            return nextState, nextString

    def epsilonStateBW(self, epsilon, listStates, currentState, dictQValues):
        x = random.uniform(0,1)
        #Fem exploració amb probabilitat epsilon
        if x < epsilon:
            n = random.randint(0, len(listStates) - 1)
            return listStates[n]
        #Fem exploració amb probabilitat 1 - epsilon
        else:
            listBestStates = []
            maxValue = -10000
            currentDict = dictQValues[currentState]
            error = 0.01
            for state in listStates:
                qValue = currentDict[state]
                if qValue <= maxValue + error and qValue >= maxValue - error:
                    listBestStates.append(state)
                elif qValue > maxValue:
                    maxValue = qValue
                    listBestStates.clear()
                    listBestStates.append(state)
                if qValue < 0:
                    listStates.pop(state)

            n = random.randint(0, len(listBestStates) - 1)
            return listBestStates[n]



    def Qlearning(self, epsilon, gamma, alpha):
        currentState = self.getCurrentStateW()
        #Transformem l'estat en un string
        currentString = self.stateToString(currentState)
        #Guardem l'estat inicial de la taula
        initialState, initialString = currentState, currentString
        self.qTable[currentString] = {}
        #Arribarem a aquest error al voltant de l'iteració 7500.
        #Aleshores, podem afirmar que el Q-learning convergeix.
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
                print(numIteracions, mitjanaDelta)

                #Si està en l'interval (-error, error), vol dir que aquest camí ha convergit.
                if mitjanaDelta < error and mitjanaDelta > -error:
                    numCaminsConvergents += 1
                #Si no, reiniciem el comptador.
                else:
                    numCaminsConvergents = 0
            self.newBoardSim(initialState+[[0,4,12]])
            currentState, currentString = initialState, initialString
        #Quan ja s'acaba l'execució, recuperem el camí que ens porta a una recompensa major.
        self.reconstructPath(initialState)
        print(numIteracions)

    def reconstructPath(self, initialState):
        currentState = initialState
        currentString = self.stateToString(initialState)
        checkMate = False

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

        print(path)

    def reconstructPathBW(self, initialState):
        currentState = initialState
        currentString = self.BWStateToString(initialState)
        checkMate = False

        #Afegim l'estat inicial
        path = [initialState]
        torn = False
        while not checkMate:
            torn = not torn
            if torn:
                currentDict = self.qTableWhites[currentString]
            else:
                currentDict = self.qTableBlacks[currentString]
            maxQ = -100000
            maxState = None
            #Mirem quin és el següent estat que té major Q-value
            for stateString in currentDict.keys():
                qValue = currentDict[stateString]
                if maxQ < qValue:
                    maxQ = qValue
                    maxState = stateString
            state = self.stringToBWState(maxState)
            #Quan l'obtenim l'agefim al path
            path.append(state)
            movement = self.getMovement(currentState,state)
            #Fem el moviment corresponent
            self.chess.move(movement[0],movement[1])
            self.chess.board.print_board()
            currentString = maxState
            currentState = state
            #Quan ja s'aconsegueix fer check mate, s'acaba l'execució.
            if torn and self.isBlackInCheckMate(state):
                checkMate = True
            if not torn and self.isWhiteInCheckMate(state):
                checkMate = True

        print(path)

    def recompensaBW(self, currentState, previousState, torn):
        bkState = self.getPieceState(currentState, 12)
        wkState = self.getPieceState(currentState, 6)
        brState = self.getPieceState(currentState, 8)
        wrState = self.getPieceState(currentState, 2)

        if self.allBkMovementsWatched(currentState) and torn:
            #Si el rei negre està en check mate
            if self.isWatchedBk(currentState):
                #Retornem recompensa i com que és un estat terminal, True.
                return 1000, True
            #Estem en empat
            else:
                #Retornem recompensa i com que és un estat terminal, True.
                return 0, True

        if self.allWkMovementsWatched(currentState) and not torn:
            # Si el rei blanc està en check mate
            if self.isWatchedWk(currentState):
                # Retornem recompensa i com que és un estat terminal, True.
                return 1000, True
            # Estem en empat
            else:
                # Retornem recompensa i com que és un estat terminal, True.
                return 0, True
        #Les dues torres estan vives
        if brState != None and wrState != None:
            #No ens interessen les dues torres vives.
            #Per tant, el cost per sobreviure és major per les blanques
            if torn:
                return -1, False
            else:
                return 1, False
        #Les dues torres estan mortes
        if brState == None and wrState == None:
            """
            previousBrState = self.getPieceState(previousState,8)
            #Les blanques han matat la torre negra.
            if previousBrState != None:
                if torn:
                    return 50, True
                else:
                    return -1000, True

            previousWrState = self.getPieceState(previousState,2)
            if previousWrState != None:
                if not torn:
                    return 50, True
                else:
                    return -1000, True

            """
            #Rei negre ha matat a la torre blanca. S'acaba la partida i compta com "mini-victòria" per les negres.
            return 100, True
        if brState == None:
            #Si les blanques maten la torre negre, ara els costa menys sobreviure.
            if torn:
                return -0.5, False
            #Ens interessa que les negres intentin sobreviure el màxim possible,
            # per tant sobreviure té un valor positiu.
            else:
                return 0.5, False
        if wrState == None:
            #Les negres han matat la torre blanca. Per tant, és torn de les negres i 'mini-victòria' per les negres
            return 100, True

    def towersAlive(self, currentState):
        return self.getPieceState(currentState,2) != None and self.getPieceState(currentState,8) != None

    def QlearningWhitesVsBlacks(self, epsilon, alpha, gamma):
        checkMate = False
        torn = True

        initialState = self.getCurrentState()
        currentState = initialState
        xState = initialState
        currentString = self.BWStateToString(currentState)
        xString = currentString
        #Restringim el número de moviments per cada partida.
        numMaxMoviments = 200

        error = 0.15
        numIteracions = 0
        numCaminsConvergents = 0

        while numIteracions < 500:
            numIteracions += 1
            if numIteracions > 2:
                print(self.qTableWhites[xString])
            if numIteracions == 99:
                self.reconstructPathBW(xState)
                initialState = [[1,0,2],[3,4,6],[0,4,12]]
            checkMate = False
            numMovimentsBlanques = 0
            numMovimentsNegres = 0
            deltaBlanques = 0
            deltaNegres = 0
            comptMoviments = 0
            while not checkMate:
                if comptMoviments >= numMaxMoviments and self.towersAlive(currentState):
                    break
                if torn:
                    # Si no hem visitat l'estat, l'afegim a la q-table
                    if currentString not in self.qTableWhites.keys():
                        self.qTableWhites[currentString] = {}

                    listNextStates = []
                    blackState = self.getBlackState(currentState)
                    brState = self.getPieceState(currentState,8)
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

                    # Triem un dels estats mitjançant exploració o explotació.
                    nextState = self.epsilonState(epsilon, listNextStates, currentState, self.qTableWhites)
                    nextString = self.BWStateToString(nextState)

                    # Si no l'hem visitat, el seu Q-value inicial és 0
                    if nextString not in self.qTableWhites[currentString].keys():
                        qValue = 0
                    else:
                        qValue = self.qTableWhites[currentString][nextString]
                    # Obtenim la recompensa associada a l'estat nextState, i si és un estat terminal
                    recompensa, isFinalState = self.recompensaBW(nextState, currentState, torn)
                    # Si tenim algun escac i mat, el Q-Value ja serà la pròpia recompensa
                    # Ja que és un estat terminal.
                    if isFinalState:
                        qValue = recompensa
                    else:
                        # Obtenim el valor de la sample i del Q-value
                        sample = recompensa - gamma * self.maxQValue(nextString, self.qTableBlacks)
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
                        checkMate = True

                else:
                    # Si no hem visitat l'estat, l'afegim a la q-table
                    if currentString not in self.qTableBlacks.keys():
                        self.qTableBlacks[currentString] = {}

                    listNextStates = []
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

                    # Triem un dels estats mitjançant exploració o explotació.
                    nextState = self.epsilonState(epsilon, listNextStates, currentState, self.qTableBlacks)
                    nextString = self.BWStateToString(nextState)

                    # Si no l'hem visitat, el seu Q-value inicial és 0
                    if nextString not in self.qTableBlacks[currentString].keys():
                        qValue = 0
                    else:
                        qValue = self.qTableBlacks[currentString][nextString]
                    # Obtenim la recompensa associada a l'estat nextState i si és un estat terminal.
                    recompensa, isFinalState = self.recompensaBW(nextState, currentState, torn)
                    # Si tenim algun escac i mat, el Q-Value ja serà la pròpia recompensa
                    # Ja que és un estat terminal.
                    if isFinalState:
                        qValue = recompensa
                    else:
                        # Obtenim el valor de la sample i del Q-value
                        sample = recompensa - gamma * self.maxQValue(nextString, self.qTableWhites)
                        deltaNegres += sample - qValue
                        qValue = (1 - alpha) * qValue + alpha * sample
                    # Actualitzem la taula
                    self.qTableBlacks[currentString][nextString] = qValue
                    if not isFinalState:
                        # Movem les fitxes a la posició actual
                        self.newBoardSim(nextState)

                        currentState, currentString = nextState, nextString
                        numMovimentsNegres += 1

                    # En cas que sigui escac i mat, acabem aquesta iteració del Q-learning.
                    else:
                        checkMate = True

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

            self.chess.boardSim.print_board()

            self.newBoardSim(initialState)
            currentState = initialState
        self.reconstructPathBW(xState)
        print("\n\n")
        self.reconstructPathBW(initialState)
        return 0



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

    numExercici = 1

    #Configuració inicial del taulell
    TA[1][0] = 2
    TA[2][4] = 6
    #TA[0][7] = 8
    TA[0][4] = 12

    # initialise board
    print("stating AI chess... ")
    aichess = Aichess(TA, True)


    print("printing board")
    aichess.chess.boardSim.print_board()

    #aichess.QlearningWhitesVsBlacks(0.4,0.9,0.1)
    aichess.Qlearning(0.3, 0.9, 0.1)




