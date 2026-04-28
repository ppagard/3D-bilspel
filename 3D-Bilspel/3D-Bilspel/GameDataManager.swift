//
//  GameDataManager.swift
//  3D-Bilspel
//

import Foundation

class GameDataManager {
    
    static let shared = GameDataManager()
    
    private let highScoreKey = "highScore_3D_Bilspel"
    
    private init() {}
    
    var highScore: Int {
        return UserDefaults.standard.integer(forKey: highScoreKey)
    }
    
    func saveHighScore(_ score: Int) {
        UserDefaults.standard.set(score, forKey: highScoreKey)
        UserDefaults.standard.synchronize()
    }
    
    func resetHighScore() {
        UserDefaults.standard.removeObject(forKey: highScoreKey)
    }
}
