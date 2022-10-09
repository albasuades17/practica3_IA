#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 11:22:03 2022

@author: ignasi
"""
import copy

import chess
import board
import numpy as np
import sys
import queue
from typing import List

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
        self.pathToTarget = []
        self.currentStateW = self.chess.boardSim.currentStateW;
        self.depthMax = 8;
        self.checkMate = False

    def getCurrentState(self):

        return self.myCurrentStateW

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

    def isWatchedBk(self, bkPosition):
        whiteState = self.chess.boardSim.currentStateW.copy()
        wkState = self.getPieceState(whiteState, 6)
        wrState = self.getPieceState(whiteState, 2)

        #Si les negres maten el rei blanc, no és una configuració correcta
        if wkState == None:
            return False
        #Mirem les possibles posicions del rei blanc i mirem si en alguna pot "matar" al rei negre
        for wkPosition in self.getNextPositions(wkState):
            if bkPosition  == wkPosition:
                #Tindríem un checkMate
                return True
        if wrState != None:
            # Mirem les possibles posicions de la torre blanca i mirem si en alguna pot "matar" al rei negre
            for wrPosition in self.getNextPositions(wrState):
                if bkPosition == wrPosition:
                    return True

        return False




    def isBlackInCheckMate(self, whiteState, blackState):
        #En aquest mètode mirem si el rei negre està amenaçat per les peces blanques
        #Agafem l'estat del rei negre
        bkState = self.getPieceState(blackState, 12)
        checkMate = False
        #Rei negre es troba a una paret, llavors es pot donar un checkMate
        if bkState[0] == 0 or bkState[0] == 7 or bkState[1] == 0 or bkState[1] == 7:
            #Obtenim l'estat de les nostres peces blanques
            wkState = self.getPieceState(whiteState, 6)
            wrState = self.getPieceState(whiteState, 2)
            checkMate = True
            #Obtenim els estats futur de les peces negres
            nextBStates = self.getListNextStatesB(blackState)

            for state in nextBStates:
                listStates = [wrState,wkState]
                bkState = self.getPieceState(state, 12)
                listStates.append(bkState)
                brState = self.getPieceState(state, 8)
                listStates.append(brState)
                # Movem les peces negres al nou state
                self.newBoardSim(listStates)
                self.chess.boardSim.print_board()

                #Comprovem si en aquesta posició el rei negre no està amenaçat, que implica que no hi haurà checkmate
                if not self.isWatchedBk(bkState[0:2]):
                    checkMate = False
                    break

        return checkMate


    def isWatchedWk(self, wkPosition):
        blackState = self.chess.boardSim.currentStateB.copy()
        bkState = self.getPieceState(blackState, 12)
        brState = self.getPieceState(blackState, 8)

        #Si les negres maten el rei blanc, no és una configuració correcta
        if bkState == None:
            return False
        #Mirem les possibles posicions del rei blanc i mirem si en alguna pot "matar" al rei negre
        for bkPosition in self.getNextPositions(bkState):
            if wkPosition  == bkPosition:
                #Tindríem un checkMate
                return True
        if brState != None:
            # Mirem les possibles posicions de la torre blanca i mirem si en alguna pot "matar" al rei negre
            for brPosition in self.getNextPositions(brState):
                if wkPosition == brPosition:
                    return True

        return False




    def isWhiteInCheckMate(self, blackState, whiteState):
        #En aquest mètode mirem si el rei negre està amenaçat per les peces blanques
        #Agafem l'estat del rei negre
        wkState = self.getPieceState(whiteState, 6)
        checkMate = False
        #Rei negre es troba a una paret, llavors es pot donar un checkMate
        if wkState[0] == 0 or wkState[0] == 7 or wkState[1] == 0 or wkState[1] == 7:
            #Obtenim l'estat de les nostres peces blanques
            bkState = self.getPieceState(blackState, 12)
            brState = self.getPieceState(blackState, 8)
            checkMate = True
            #Obtenim els estats futur de les peces negres
            nextWStates = self.getListNextStatesW(whiteState)
            for state in nextWStates:
                listStates = [brState,bkState]
                wkState = self.getPieceState(state, 6)
                listStates.append(wkState)
                wrState = self.getPieceState(state, 2)
                listStates.append(wrState)
                # Movem les peces negres al nou state
                self.newBoardSim(listStates)
                self.chess.boardSim.print_board()
                #Comprovem si en aquesta posició el rei negre no està amenaçat, que implica que no hi haurà checkmate
                if not self.isWatchedWk(wkState[0:2]):
                    checkMate = False
                    break

        return checkMate


    def newBoardSim(self, listStates):
        #Creem una nova board
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

    def getNextPositions(self, state):
        #Donat un estat, mirem els següents possibles estats
        #A partir d'aquests retornem una llista amb les posicions, és a dir, [fila,columna]
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
    # white pieces
    # TA[0][0] = 2
    # TA[2][4] = 6
    # # black pieces
    # TA[0][4] = 12

    TA[0][7] = 8
    TA[4][5] = 12
    TA[5][7] = 2
    TA[4][7] = 6

    # initialise board
    print("stating AI chess... ")
    aichess = Aichess(TA, True)
    currentState = aichess.chess.board.currentStateW.copy()

    print("printing board")
    aichess.chess.boardSim.print_board()

    # get list of next states for current state
    print("current State", currentState)

    #call checkmate method
    whiteState = aichess.chess.board.currentStateW.copy()
    blackState = aichess.chess.board.currentStateB.copy()
    #print(aichess.isBlackInCheckMate(whiteState, blackState))
    print(aichess.isWhiteInCheckMate(blackState, whiteState))

