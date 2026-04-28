//
//  GameDelegate.swift
//  3D-Bilspel
//

import Foundation

protocol GameDelegate: AnyObject {
    func didStartGame()
    func didGameOver(score: Int, highScore: Int)
}
