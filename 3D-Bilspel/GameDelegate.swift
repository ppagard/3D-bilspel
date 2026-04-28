//
//  GameDelegate.swift
//  3D-Bilspel
//
//  Protokoll för spelhändelser
//

import Foundation

protocol GameDelegate: AnyObject {
    func didStartGame()
    func didGameOver(score: Int, highScore: Int)
}
