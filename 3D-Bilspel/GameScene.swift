//
//  GameScene.swift
//  3D-Bilspel
//
//  Huvudspel-scen med SceneKit
//

import Foundation
import UIKit
import SceneKit

protocol GameSceneDelegate: AnyObject {
    func didStartGame()
    func didGameOver(score: Int, highScore: Int)
}

class GameScene: SCNScene {
    
    weak var gameDelegate: GameSceneDelegate?
    
    // Spelstatus
    private var isPlaying = false
    private var isPaused = false
    private var score = 0
    private var speed: Float = 1.0
    private var baseSpeed: Float = 1.0
    private var maxSpeed: Float = 4.0
    private var distanceTravelled: Float = 0
    
    // 3D-objekt
    var car: SCNNode!
    var roadNode: SCNNode!
    var leftRoadNode: SCNNode!
    var rightRoadNode: SCNNode!
    var leftBarrierNode: SCNNode!
    var rightBarrierNode: SCNNode!
    
    // Lanes: -2 (vänster), 0 (mitten), 2 (höger)
    private let lanePositions: [Float] = [-2.0, 0.0, 2.0]
    private var currentLane = 1 // mitten
    private var targetX: Float = 0.0
    private var isTransitioning = false
    
    // Obstacles
    private var obstacles: [SCNNode] = []
    private var obstacleSpawnTimer: TimeInterval = 0
    private var obstacleSpawnInterval: TimeInterval = 1.5
    private var nextObstacleZ: Float = -30.0
    
    // Road segments for scrolling
    private var roadSegments: [SCNNode] = []
    private let roadSegmentLength: Float = 20.0
    private let roadWidth: Float = 14.0
    
    // Ground segments
    private var groundSegments: [SCNNode] = []
    
    // Lighting
    var ambientLightNode: SCNNode!
    var directionalLightNode: SCNNode!
    
    // Camera
    var cameraNode: SCNNode!
    
    // Touch handling
    private var touchStartX: CGFloat = 0
    
    // Skybox color animation
    private var skyColorTarget = SCNColor(0.4, 0.7, 0.9, 1.0)
    
    override init() {
        super.init()
        createScene()
    }
    
    required init?(coder: NSCoder) {
        super.init(coder: coder)
    }
    
    private func createScene() {
        // Camera
        cameraNode = SCNNode()
        cameraNode.camera = SCNCamera()
        cameraNode.camera?.zNear = 0.1
        cameraNode.camera?.zFar = 200
        cameraNode.position = SCNVector3(0, 5, 10)
        cameraNode.rotation = SCNVector4(1, 0, 0, -30 * .pi / 180)
        rootNode.addChildNode(cameraNode)
        
        // Lighting
        ambientLightNode = SCNNode()
        ambientLightNode.light = SCNLight()
        ambientLightNode.light?.type = .ambient
        ambientLightNode.light?.ambientColor = SCNColor(0.4, 0.4, 0.5, 1.0)
        ambientLightNode.position = SCNVector3(0, 10, 0)
        rootNode.addChildNode(ambientLightNode)
        
        directionalLightNode = SCNNode()
        directionalLightNode.light = SCNLight()
        directionalLightNode.light?.type = .directional
        directionalLightNode.light?.intensity = 800
        directionalLightNode.light?.color = SCNColor(1.0, 0.95, 0.8, 1.0)
        directionalLightNode.rotation = SCNVector4(1, -0.5, 0, 45 * .pi / 180)
        rootNode.addChildNode(directionalLightNode)
        
        // Create the car
        createCar()
        
        // Create road
        createRoad()
        
        // Create ground
        createGround()
        
        // Create environment (mountains/hills)
        createEnvironment()
    }
    
    private func createCar() {
        car = SCNNode()
        
        // Car body
        let bodyGeometry = SCNBox(width: 1.8, height: 0.6, length: 3.2, chamferRadius: 0.05)
        let bodyMaterial = SCNMaterial()
        bodyMaterial.diffuse.contents = UIColor(red: 0.9, green: 0.1, blue: 0.1, alpha: 1.0)
        bodyMaterial.specular.contents = UIColor.white
        bodyMaterial.metallic = 0.6
        bodyGeometry.materials = [bodyMaterial]
        let bodyNode = SCNNode(geometry: bodyGeometry)
        bodyNode.position = SCNVector3(0, 0.5, 0)
        car.addChildNode(bodyNode)
        
        // Car cabin
        let cabinGeometry = SCNBox(width: 1.4, height: 0.5, length: 1.6, chamferRadius: 0.05)
        let cabinMaterial = SCNMaterial()
        cabinMaterial.diffuse.contents = UIColor(red: 0.7, green: 0.1, blue: 0.1, alpha: 1.0)
        cabinMaterial.specular.contents = UIColor.white
        cabinMaterial.metallic = 0.4
        cabinGeometry.materials = [cabinMaterial]
        let cabinNode = SCNNode(geometry: cabinGeometry)
        cabinNode.position = SCNVector3(0, 1.05, -0.2)
        car.addChildNode(cabinNode)
        
        // Windshield
        let windshieldGeometry = SCNBox(width: 1.2, height: 0.4, length: 0.05, chamferRadius: 0.0)
        let windshieldMaterial = SCNMaterial()
        windshieldMaterial.diffuse.contents = UIColor(red: 0.3, green: 0.6, blue: 0.9, alpha: 0.6)
        windshieldMaterial.transparency = 0.4
        windshieldGeometry.materials = [windshieldMaterial]
        let windshieldNode = SCNNode(geometry: windshieldGeometry)
        windshieldNode.position = SCNVector3(0, 1.0, 0.6)
        windshieldNode.rotation = SCNVector4(1, 0, 0, 15 * .pi / 180)
        car.addChildNode(windshieldNode)
        
        // Wheels
        let wheelGeometry = SCNCylinder(radius: 0.25, height: 0.2, chamferRadius: 0.02)
        let wheelMaterial = SCNMaterial()
        wheelMaterial.diffuse.contents = UIColor.darkGray
        wheelMaterial.specular.contents = UIColor.gray
        wheelMaterial.metallic = 0.8
        wheelGeometry.materials = [wheelMaterial]
        
        let wheelPositions = [
            SCNVector3(-0.9, 0.25, 1.0),
            SCNVector3(0.9, 0.25, 1.0),
            SCNVector3(-0.9, 0.25, -1.0),
            SCNVector3(0.9, 0.25, -1.0)
        ]
        
        for pos in wheelPositions {
            let wheelNode = SCNNode(geometry: wheelGeometry)
            wheelNode.position = pos
            wheelNode.rotation = SCNVector4(0, 0, 1, .pi / 2)
            car.addChildNode(wheelNode)
        }
        
        // Headlights
        let lightGeometry = SCNSphere(radius: 0.12, chamferRadius: 0.02)
        let lightMaterial = SCNMaterial()
        lightMaterial.diffuse.contents = UIColor.yellow
        lightMaterial.emission.contents = UIColor.yellow
        lightMaterial.intensity = 5.0
        lightGeometry.materials = [lightMaterial]
        
        let leftLight = SCNNode(geometry: lightGeometry)
        leftLight.position = SCNVector3(-0.6, 0.5, 1.65)
        car.addChildNode(leftLight)
        
        let rightLight = SCNNode(geometry: lightGeometry)
        rightLight.position = SCNVector3(0.6, 0.5, 1.65)
        car.addChildNode(rightLight)
        
        // Taillights
        let tailMaterial = SCNMaterial()
        tailMaterial.diffuse.contents = UIColor(red: 1.0, green: 0.0, blue: 0.0, alpha: 1.0)
        tailMaterial.emission.contents = UIColor(red: 1.0, green: 0.0, blue: 0.0, alpha: 1.0)
        tailMaterial.intensity = 3.0
        
        let leftTail = SCNNode(geometry: lightGeometry)
        leftTail.position = SCNVector3(-0.6, 0.5, -1.65)
        leftTail.geometry?.materials = [tailMaterial]
        car.addChildNode(leftTail)
        
        let rightTail = SCNNode(geometry: lightGeometry)
        rightTail.position = SCNVector3(0.6, 0.5, -1.65)
        rightTail.geometry?.materials = [tailMaterial]
        car.addChildNode(rightTail)
        
        car.position = SCNVector3(0, 0, 0)
        rootNode.addChildNode(car)
    }
    
    private func createRoad() {
        // Clear existing
        for segment in roadSegments {
            rootNode.removeChildNode(segment)
        }
        roadSegments.removeAll()
        
        // Create road segments along Z axis
        for i in 0..<5 {
            let segment = createRoadSegment(z: -Float(i) * roadSegmentLength)
            roadSegments.append(segment)
            rootNode.addChildNode(segment)
        }
    }
    
    private func createRoadSegment(z: Float) -> SCNNode {
        let group = SCNNode()
        
        // Main road
        let roadGeometry = SCNPlane(width: roadWidth, height: roadSegmentLength)
        let roadMaterial = SCNMaterial()
        roadMaterial.diffuse.contents = UIColor.darkGray
        roadMaterial.specular.contents = UIColor.gray
        roadMaterial.metallic = 0.2
        roadGeometry.materials = [roadMaterial]
        
        let roadNode = SCNNode(geometry: roadGeometry)
        roadNode.rotation = SCNVector4(1, 0, 0, -90 * .pi / 180)
        roadNode.position = SCNVector3(0, 0.01, z)
        group.addChildNode(roadNode)
        
        // Lane markings (dashed white lines)
        let lineMaterial = SCNMaterial()
        lineMaterial.diffuse.contents = UIColor.white
        lineMaterial.emission.contents = UIColor.white
        lineMaterial.intensity = 0.5
        
        for laneX in [-1.0, 1.0] {
            for j in 0..<4 {
                let lineGeometry = SCNPlane(width: 0.15, height: 2.0)
                let lineNode = SCNNode(geometry: lineGeometry)
                lineNode.rotation = SCNVector4(1, 0, 0, -90 * .pi / 180)
                lineNode.position = SCNVector3(laneX, 0.02, z - roadSegmentLength/2 + 2.5 + Float(j) * 4.5)
                lineNode.geometry?.materials = [lineMaterial]
                group.addChildNode(lineNode)
            }
        }
        
        // Road edges (solid white lines)
        for edgeX in [-roadWidth/2 + 0.1, roadWidth/2 - 0.1] {
            let edgeGeometry = SCNPlane(width: 0.1, height: roadSegmentLength)
            let edgeNode = SCNNode(geometry: edgeGeometry)
            edgeNode.rotation = SCNVector4(1, 0, 0, -90 * .pi / 180)
            edgeNode.position = SCNVector3(edgeX, 0.02, z)
            edgeNode.geometry?.materials = [lineMaterial]
            group.addChildNode(edgeNode)
        }
        
        return group
    }
    
    private func createGround() {
        for i in 0..<5 {
            let groundGroup = SCNNode()
            
            // Left ground
            let leftGroundGeom = SCNPlane(width: 50, height: roadSegmentLength)
            let groundMaterial = SCNMaterial()
            groundMaterial.diffuse.contents = UIColor(red: 0.25, green: 0.6, blue: 0.2, alpha: 1.0)
            leftGroundGeom.materials = [groundMaterial]
            let leftGround = SCNNode(geometry: leftGroundGeom)
            leftGround.rotation = SCNVector4(1, 0, 0, -90 * .pi / 180)
            leftGround.position = SCNVector3(-32, -0.01, -Float(i) * roadSegmentLength)
            groundGroup.addChildNode(leftGround)
            
            // Right ground
            let rightGround = SCNNode(geometry: leftGroundGeom)
            rightGround.rotation = SCNVector4(1, 0, 0, -90 * .pi / 180)
            rightGround.position = SCNVector3(32, -0.01, -Float(i) * roadSegmentLength)
            groundGroup.addChildNode(rightGround)
            
            groundSegments.append(groundGroup)
            rootNode.addChildNode(groundGroup)
        }
    }
    
    private func createEnvironment() {
        // Add some mountains/hills in the distance
        for i in 0..<10 {
            let angle = Float(i) * .pi * 2 / 10
            let radius: Float = 60 + Float.random(in: 0...20)
            let x = cos(Double(angle)) * Double(radius)
            let z = sin(Double(angle)) * Double(radius) - 80
            
            let mountainHeight: Float = Float.random(in: 8...20)
            let mountainGeom = SCNCone(topRadius: 0, bottomRadius: 15, height: mountainHeight, chamferRadius: 0)
            let mountainMat = SCNMaterial()
            
            let greenValue: Float = Float.random(in: 0.15...0.35)
            mountainMat.diffuse.contents = UIColor(red: greenValue, green: greenValue + 0.2, blue: greenValue + 0.05, alpha: 1.0)
            mountainGeom.materials = [mountainMat]
            
            let mountainNode = SCNNode(geometry: mountainGeom)
            mountainNode.position = SCNVector3(Float(x), mountainHeight / 2 - 2, Float(z))
            rootNode.addChildNode(mountainNode)
        }
        
        // Trees along the road
        for i in 0..<30 {
            let z = -Float(i) * 6 + Float.random(in: -2...2)
            
            // Left side trees
            createTree(atX: -roadWidth/2 - 2 - Float.random(in: 0...5), atZ: z)
            // Right side trees
            createTree(atX: roadWidth/2 + 2 + Float.random(in: 0...5), atZ: z)
        }
    }
    
    private func createTree(atX: Float, atZ: Float) {
        let treeGroup = SCNNode()
        
        // Trunk
        let trunkGeom = SCNCylinder(radius: 0.2, height: 2.5, chamferRadius: 0.05)
        let trunkMat = SCNMaterial()
        trunkMat.diffuse.contents = UIColor(brownColor)
        trunkGeom.materials = [trunkMat]
        let trunk = SCNNode(geometry: trunkGeom)
        trunk.position = SCNVector3(0, 1.25, 0)
        treeGroup.addChildNode(trunk)
        
        // Foliage (multiple spheres for a fuller look)
        let foliageMat = SCNMaterial()
        let green = Float.random(in: 0.2...0.45)
        foliageMat.diffuse.contents = UIColor(red: 0.1, green: green, blue: 0.05, alpha: 1.0)
        
        let sizes: [(Float, Float, Float)] = [(1.5, 1.5, 2.5), (1.2, 1.2, 3.5), (0.8, 0.8, 4.5)]
        for (r, h, y) in sizes {
            let foliageGeom = SCNSphere(radius: r, chamferRadius: 0.3)
            foliageGeom.materials = [foliageMat]
            let foliage = SCNNode(geometry: foliageGeom)
            foliage.position = SCNVector3(0, y, 0)
            treeGroup.addChildNode(foliage)
        }
        
        treeGroup.position = SCNVector3(atX, 0, atZ)
        rootNode.addChildNode(treeGroup)
    }
    
    // MARK: - Game Control
    
    func startGame() {
        isPlaying = true
        isPaused = false
        score = 0
        speed = baseSpeed
        distanceTravelled = 0
        obstacleSpawnTimer = 0
        obstacleSpawnInterval = 1.5
        nextObstacleZ = -30.0
        
        currentLane = 1
        targetX = lanePositions[currentLane]
        car.position.x = targetX
        car.rotation = SCNVector4(0, 0, 0, 0)
        
        // Clear old obstacles
        for obstacle in obstacles {
            rootNode.removeChildNode(obstacle)
        }
        obstacles.removeAll()
        
        // Reset road
        for (i, segment) in roadSegments.enumerated() {
            segment.position.z = -Float(i) * roadSegmentLength
        }
        
        for (i, segment) in groundSegments.enumerated() {
            segment.position.z = -Float(i) * roadSegmentLength
        }
        
        gameDelegate?.didStartGame()
    }
    
    func updateGame(dt: TimeInterval) {
        guard isPlaying else { return }
        
        // Update road scrolling
        updateRoad(dt)
        
        // Move car forward (in world space, car moves in -Z direction)
        let moveDistance = speed * Float(dt) * 15
        car.position.z -= moveDistance
        distanceTravelled += moveDistance
        
        // Smooth lane transition
        if isTransitioning {
            let transitionSpeed: Float = 12.0
            let diff = targetX - car.position.x
            let step = diff * min(1.0, transitionSpeed * Float(dt))
            car.position.x += step
            
            // Car tilt during turn
            let tiltAngle = step * 80.0
            car.rotation = SCNVector4(0, 0, 1, -tiltAngle * .pi / 180)
            
            if abs(diff) < 0.01 {
                car.position.x = targetX
                isTransitioning = false
                car.rotation = SCNVector4(0, 0, 0, 0)
            }
        }
        
        // Car bobbing animation
        car.position.y = sin(Double(distanceTravelled) * 3.0) * 0.02
        
        // Increase speed over time
        speed = min(maxSpeed, baseSpeed + distanceTravelled * 0.003)
        
        // Spawn obstacles
        obstacleSpawnTimer += dt
        if obstacleSpawnTimer >= obstacleSpawnInterval {
            obstacleSpawnTimer = 0
            spawnObstacle()
            // Decrease spawn interval as speed increases
            obstacleSpawnInterval = max(0.6, 1.5 - distanceTravelled * 0.002)
        }
        
        // Update obstacles
        updateObstacles(dt)
        
        // Update score
        score = Int(distanceTravelled * 10)
        
        // Camera follow
        if let camera = cameraNode.camera {
            camera.zNear = 0.1
            camera.zFar = 200
        }
        cameraNode.position.x = car.position.x * 0.3
        cameraNode.position.y = 5 + car.position.y
        cameraNode.position.z = car.position.z + 10
        cameraNode.look(at: SCNVector3(car.position.x, 1, car.position.z - 20))
    }
    
    private func updateRoad(dt: TimeInterval) {
        let moveDistance = speed * Float(dt) * 15
        
        for segment in roadSegments {
            segment.position.z += moveDistance
            if segment.position.z > roadSegmentLength {
                segment.position.z -= Float(roadSegments.count) * roadSegmentLength
            }
        }
        
        for segment in groundSegments {
            segment.position.z += moveDistance
            if segment.position.z > roadSegmentLength {
                segment.position.z -= Float(groundSegments.count) * roadSegmentLength
            }
        }
    }
    
    private func spawnObstacle() {
        let laneIndex = Int.random(in: 0...2)
        let laneX = lanePositions[laneIndex]
        
        let obstacleType = Int.random(in: 0...2)
        var obstacleNode: SCNNode
        
        switch obstacleType {
        case 0:
            // Car obstacle (different color)
            obstacleNode = createCarObstacle()
        case 1:
            // Barrier
            obstacleNode = createBarrierObstacle()
        default:
            // Rock
            obstacleNode = createRockObstacle()
        }
        
        obstacleNode.position = SCNVector3(laneX, 0, nextObstacleZ)
        obstacleNode.userData = ["type": "obstacle", "speed": speed, "lane": laneIndex]
        obstacles.append(obstacleNode)
        rootNode.addChildNode(obstacleNode)
        
        nextObstacleZ -= roadSegmentLength * 0.8
    }
    
    private func createCarObstacle() -> SCNNode {
        let carColor = UIColor.randomCarColor()
        let node = SCNNode()
        
        let bodyGeom = SCNBox(width: 1.8, height: 0.6, length: 3.2, chamferRadius: 0.05)
        let bodyMat = SCNMaterial()
        bodyMat.diffuse.contents = carColor
        bodyMat.specular.contents = UIColor.white
        bodyMat.metallic = 0.5
        bodyGeom.materials = [bodyMat]
        let body = SCNNode(geometry: bodyGeom)
        body.position = SCNVector3(0, 0.5, 0)
        node.addChildNode(body)
        
        // Wheels
        let wheelGeom = SCNCylinder(radius: 0.25, height: 0.2, chamferRadius: 0.02)
        let wheelMat = SCNMaterial()
        wheelMat.diffuse.contents = UIColor.darkGray
        wheelGeom.materials = [wheelMat]
        
        for wx in [-0.9, 0.9] {
            for wz in [-1.0, 1.0] {
                let wheel = SCNNode(geometry: wheelGeom)
                wheel.position = SCNVector3(wx, 0.25, wz)
                wheel.rotation = SCNVector4(0, 0, 1, .pi / 2)
                node.addChildNode(wheel)
            }
        }
        
        return node
    }
    
    private func createBarrierObstacle() -> SCNNode {
        let node = SCNNode()
        
        let barrierGeom = SCNBox(width: 2.5, height: 0.8, length: 0.5, chamferRadius: 0.02)
        let barrierMat = SCNMaterial()
        barrierMat.diffuse.contents = UIColor(red: 0.9, green: 0.5, blue: 0.1, alpha: 1.0)
        barrierMat.emission.contents = UIColor(red: 0.9, green: 0.5, blue: 0.1, alpha: 0.3)
        barrierGeom.materials = [barrierMat]
        let barrier = SCNNode(geometry: barrierGeom)
        barrier.position = SCNVector3(0, 0.4, 0)
        node.addChildNode(barrier)
        
        // Stripes
        for i in -2...2 {
            let stripeGeom = SCNBox(width: 0.2, height: 0.8, length: 0.52, chamferRadius: 0)
            let stripeMat = SCNMaterial()
            stripeMat.diffuse.contents = UIColor.white
            stripeGeom.materials = [stripeMat]
            let stripe = SCNNode(geometry: stripeGeom)
            stripe.position = SCNVector3(Float(i) * 0.5, 0.4, 0)
            node.addChildNode(stripe)
        }
        
        return node
    }
    
    private func createRockObstacle() -> SCNNode {
        let rockSize: Float = Float.random(in: 0.4...0.8)
        let rockGeom = SCNSphere(radius: rockSize, chamferRadius: 0.3)
        let rockMat = SCNMaterial()
        let gray = Float.random(in: 0.3...0.5)
        rockMat.diffuse.contents = UIColor(red: gray, green: gray, blue: gray + 0.05, alpha: 1.0)
        rockMat.specular.contents = UIColor.gray
        rockMat.metallic = 0.1
        rockGeom.materials = [rockMat]
        
        let rock = SCNNode(geometry: rockGeom)
        rock.position = SCNVector3(0, rockSize * 0.6, 0)
        rock.rotation = SCNVector4(Float.random(in: -0.5...0.5), Float.random(in: -0.5...0.5), Float.random(in: -0.5...0.5), 0)
        
        return rock
    }
    
    private func updateObstacles(dt: TimeInterval) {
        let moveDistance = speed * Float(dt) * 15
        
        for i in (0..<obstacles.count).reversed() {
            obstacles[i].position.z += moveDistance
            
            // Check collision
            if checkCollision(with: obstacles[i]) {
                gameOver()
                return
            }
            
            // Remove if passed camera
            if obstacles[i].position.z > cameraNode.position.z + 5 {
                rootNode.removeChildNode(obstacles[i])
                obstacles.remove(at: i)
                score += 50 // Bonus for passing obstacle
            }
        }
    }
    
    private func checkCollision(with obstacle: SCNNode) -> Bool {
        let carMinX = car.position.x - 0.8
        let carMaxX = car.position.x + 0.8
        let carMinZ = car.position.z - 1.5
        let carMaxZ = car.position.z + 1.5
        
        let obsMinX = obstacle.position.x - 0.9
        let obsMaxX = obstacle.position.x + 0.9
        let obsMinZ = obstacle.position.z - 1.5
        let obsMaxZ = obstacle.position.z + 1.5
        
        return carMinX < obsMaxX && carMaxX > obsMinX &&
               carMinZ < obsMaxZ && carMaxZ > obsMinZ
    }
    
    private func gameOver() {
        isPlaying = false
        
        let highScore = GameDataManager.shared.highScore
        if score > highScore {
            GameDataManager.shared.saveHighScore(score)
        }
        
        gameDelegate?.didGameOver(score: score, highScore: max(highScore, score))
    }
    
    // MARK: - Input Handling
    
    func moveLeft() {
        guard isPlaying else { return }
        if currentLane > 0 {
            currentLane -= 1
            targetX = lanePositions[currentLane]
            isTransitioning = true
        }
    }
    
    func moveRight() {
        guard isPlaying else { return }
        if currentLane < 2 {
            currentLane += 1
            targetX = lanePositions[currentLane]
            isTransitioning = true
        }
    }
    
    func handleTap(at location: CGPoint) {
        guard isPlaying else { return }
        
        let screenX = location.x
        let screenWidth = UIScreen.main.bounds.width
        
        if screenX < screenWidth / 3 {
            moveLeft()
        } else if screenX > screenWidth * 2 / 3 {
            moveRight()
        }
    }
}

// MARK: - UIColor Extensions

extension UIColor {
    static var brownColor: UIColor {
        return UIColor(red: 0.35, green: 0.2, blue: 0.1, alpha: 1.0)
    }
    
    static func randomCarColor() -> UIColor {
        let colors: [UIColor] = [
            UIColor(red: 0.1, green: 0.3, blue: 0.9, alpha: 1.0),    // Blue
            UIColor(red: 0.1, green: 0.8, blue: 0.3, alpha: 1.0),    // Green
            UIColor(red: 0.9, green: 0.8, blue: 0.1, alpha: 1.0),    // Yellow
            UIColor(red: 0.5, green: 0.1, blue: 0.8, alpha: 1.0),    // Purple
            UIColor(red: 1.0, green: 0.5, blue: 0.0, alpha: 1.0),    // Orange
            UIColor(red: 0.0, green: 0.6, blue: 0.6, alpha: 1.0),    // Teal
            UIColor(red: 0.8, green: 0.1, blue: 0.4, alpha: 1.0),    // Pink
            UIColor(red: 0.3, green: 0.3, blue: 0.3, alpha: 1.0),    // Dark gray
        ]
        return colors[Int.random(in: 0..<colors.count)]
    }
}
