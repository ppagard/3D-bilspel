//
//  GameViewController.swift
//  3D-Bilspel
//
//  3D bilspel med SceneKit
//

import UIKit
import SceneKit

class GameViewController: UIViewController {
    
    var gameScene: GameScene!
    var gameView: SCNView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupSceneView()
    }
    
    override func viewWillLayoutSubviews() {
        super.viewWillLayoutSubviews()
        gameView.scene?.rendererDelegate?.renderer?(gameView, willRender: nil, at: nil)
    }
    
    override var supportedInterfaceOrientations: UIInterfaceOrientationMask {
        return .portrait
    }
    
    override var prefersStatusBarHidden: Bool {
        return true
    }
    
    private func setupSceneView() {
        gameView = SCNView(frame: view.bounds)
        gameView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        gameView.translatesAutoresizingMaskIntoConstraints = false
        gameView.delegate = self
        gameView.allowsCameraControl = false
        gameView.showsStatistics = false
        gameView.backgroundColor = UIColor(red: 0.4, green: 0.7, blue: 0.9, alpha: 1.0)
        gameView.scene = SCNScene()
        
        gameScene = GameScene(scene: SCNScene())
        gameScene.gameDelegate = self
        gameScene.scaleMode = .automatic
        
        gameView.scene = gameScene
        
        view.addSubview(gameView)
        
        let menuScene = SCNScene(named: "scnassets/MenuScene.scn", in: nil)
        let menuView = SCNView(frame: view.bounds)
        menuView.scene = menuScene
        menuView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        menuView.translatesAutoresizingMaskIntoConstraints = false
        menuView.allowsCameraControl = false
        menuView.showsStatistics = false
        menuView.backgroundColor = UIColor(red: 0.4, green: 0.7, blue: 0.9, alpha: 1.0)
        
        view.addSubview(menuView)
        
        let playButton = UIButton(type: .system)
        playButton.setTitle("SPELA", for: .normal)
        playButton.titleLabel?.font = UIFont.systemFont(ofSize: 36, weight: .bold)
        playButton.backgroundColor = UIColor(red: 0.2, green: 0.8, blue: 0.3, alpha: 0.9)
        playButton.setTitleColor(.white, for: .normal)
        playButton.layer.cornerRadius = 15
        playButton.frame = CGRect(x: 0, y: 0, width: 200, height: 60)
        playButton.center = CGPoint(x: view.bounds.midX, y: view.bounds.midY + 100)
        playButton.addTarget(self, action: #selector(startGame), for: .touchUpInside)
        
        view.addSubview(playButton)
    }
    
    @objc private func startGame() {
        gameView.removeFromSuperview()
        for subview in view.subviews where subview is UIButton {
            subview.removeFromSuperview()
        }
        
        gameScene = GameScene(scene: SCNScene())
        gameScene.gameDelegate = self
        gameScene.scaleMode = .automatic
        
        gameView.scene = gameScene
        view.addSubview(gameView)
        gameView.isHidden = false
        
        gameScene.startGame()
    }
}

extension GameViewController: SCNSceneRendererDelegate {
    func renderer(_ renderer: SCNSceneRenderer, updateAt time: TimeInterval) {
        (gameScene as? GameScene)?.updateGame(dt: 1.0/60.0)
    }
    
    func renderer(_ renderer: SCNSceneRenderer, didRenderScene scene: SCNScene, at time: TimeInterval) {
    }
}

extension GameViewController: GameDelegate {
    func didStartGame() {
    }
    
    func didGameOver(score: Int, highScore: Int) {
        showGameOverView(score: score, highScore: highScore)
    }
    
    private func showGameOverView(score: Int, highScore: Int) {
        let overlay = UIView(frame: view.bounds)
        overlay.backgroundColor = UIColor.black.withAlphaComponent(0.7)
        overlay.tag = 999
        
        let containerView = UIView()
        containerView.backgroundColor = UIColor(white: 0.15, alpha: 1.0)
        containerView.layer.cornerRadius = 20
        containerView.frame = CGRect(x: 40, y: view.bounds.midY - 120, width: view.bounds.width - 80, height: 240)
        
        let scoreLabel = UILabel()
        scoreLabel.text = "Poäng"
        scoreLabel.font = UIFont.systemFont(ofSize: 24, weight: .light)
        scoreLabel.textColor = .white
        scoreLabel.textAlignment = .center
        scoreLabel.frame = CGRect(x: 0, y: 20, width: containerView.bounds.width, height: 30)
        
        let scoreValueLabel = UILabel()
        scoreValueLabel.text = "\(score)"
        scoreValueLabel.font = UIFont.systemFont(ofSize: 56, weight: .bold)
        scoreValueLabel.textColor = .white
        scoreValueLabel.textAlignment = .center
        scoreValueLabel.frame = CGRect(x: 0, y: 50, width: containerView.bounds.width, height: 70)
        
        let highScoreLabel = UILabel()
        highScoreLabel.text = "Rekord: \(highScore)"
        highScoreLabel.font = UIFont.systemFont(ofSize: 20, weight: .light)
        highScoreLabel.textColor = UIColor(red: 0.9, green: 0.7, blue: 0.2, alpha: 1.0)
        highScoreLabel.textAlignment = .center
        highScoreLabel.frame = CGRect(x: 0, y: 130, width: containerView.bounds.width, height: 30)
        
        let playAgainButton = UIButton(type: .system)
        playAgainButton.setTitle("SPELA IGEN", for: .normal)
        playAgainButton.titleLabel?.font = UIFont.systemFont(ofSize: 28, weight: .bold)
        playAgainButton.backgroundColor = UIColor(red: 0.2, green: 0.8, blue: 0.3, alpha: 0.9)
        playAgainButton.setTitleColor(.white, for: .normal)
        playAgainButton.layer.cornerRadius = 15
        playAgainButton.frame = CGRect(x: 20, y: 170, width: containerView.bounds.width - 40, height: 55)
        playAgainButton.addTarget(self, action: #selector(restartGame), for: .touchUpInside)
        
        containerView.addSubview(scoreLabel)
        containerView.addSubview(scoreValueLabel)
        containerView.addSubview(highScoreLabel)
        containerView.addSubview(playAgainButton)
        overlay.addSubview(containerView)
        view.addSubview(overlay)
    }
    
    @objc private func restartGame() {
        if let overlay = view.viewWithTag(999) {
            overlay.removeFromSuperview()
        }
        gameScene?.startGame()
    }
}
