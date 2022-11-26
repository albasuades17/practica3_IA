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
        #Donat un estat, la torre es pot moure a 14 llocs diferents, i el rei a 8, com a màxim.
        self.qTable = {}


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

    def maxQValue(self, stringState):
        if stringState not in self.qTable.keys():
            return 0
        maxQ = -100000
        dictState = self.qTable[stringState]
        for nextString in dictState.keys():
            maxQ = max(maxQ, dictState[nextString])
        return maxQ

    def epsilonState(self, epsilon, listStates, currentState):
        x = random.randrange(0,1)
        if x < epsilon:
            n = random.randint(0, len(listStates) - 1)
            return listStates[n]
        else:
            listBestStates = []
            maxValue = -10000
            currentDict = self.qTable[currentState]
            error = 0.01
            for state in listStates:
                qValue = currentDict[state]
                if qValue <= maxValue + error and qValue >= maxValue - error:
                    listBestStates.append(state)
                elif qValue > maxValue:
                    maxValue = qValue
                    listBestStates.clear()
                    listBestStates.append(state)

            n = random.randint(0, len(listBestStates) - 1)
            return listBestStates[n]



    def QLearning1(self, epsilon, gamma, alpha):
        currentState = self.getCurrentStateW()
        currentString = self.stateToString(currentState)
        initialState = currentState
        self.qTable[currentString] = {}

        for iteration in range (1000):
            checkMate = False
            while not checkMate:
                if currentString not in self.qTable.keys():
                    self.qTable[currentString] = {}
                listNextStates = []
                for state in self.getListNextStatesW(currentState):
                    if state[0][0:2] != [0,4] and state[1][0:2] != [0,4]:
                        listNextStates.append(state)


                nextState = self.epsilonState(epsilon, listNextStates, currentState)
                nextString = self.stateToString(nextState)

                if nextString not in self.qTable[currentString].keys():
                    qValue = 0
                else:
                    qValue = self.qTable[currentString][nextString]

                recompensa = self.recompensa(nextState)
                if recompensa != -1:
                    qValue = recompensa
                else:
                    sample = recompensa + gamma*self.maxQValue(nextString)
                    qValue = (1-alpha)*qValue + alpha*sample

                self.qTable[currentString][nextString] = qValue
                self.newBoardSim(nextState+[[0,4,12]])
                #self.chess.boardSim.print_board()
                currentState, currentString = nextState, nextString
                if recompensa != -1:
                    checkMate = True

        print(self.qTable)
        self.reconstructPath(initialState)

    def reconstructPath(self, initialState):
        currentState = initialState
        currentString = self.stateToString(initialState)
        checkMate = False
        path = [initialState]
        while not checkMate:
            currentDict = self.qTable[currentString]
            maxQ = -100000
            maxState = None
            for stateString in currentDict.keys():
                qValue = currentDict[stateString]
                if maxQ < qValue:
                    maxQ = qValue
                    maxState = stateString
            state = self.stringToState(maxState)
            path.append(state)
            movement = self.getMovement(currentState,state)
            self.chess.move(movement[0],movement[1])
            self.chess.board.print_board()
            currentString = maxState
            currentState = state
            if self.isCheckMate(state):
                checkMate = True

        print(path)


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
    TA[7][0] = 2
    TA[7][4] = 6
    #TA[0][7] = 8
    TA[0][4] = 12

    # initialise board
    print("stating AI chess... ")
    aichess = Aichess(TA, True)

    print("printing board")
    aichess.chess.boardSim.print_board()

    aichess.QLearning1(0.4, 0.9, 0.1)



