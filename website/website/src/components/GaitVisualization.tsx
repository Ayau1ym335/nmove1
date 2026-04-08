import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float } from '@react-three/drei';
import * as THREE from 'three';

function DataPoints() {
  const groupRef = useRef<THREE.Group>(null);
  const pointsRef = useRef<THREE.Points>(null);

  // Generate gait-like data points in 3D space
  const { positions, colors } = useMemo(() => {
    const count = 200;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    // Create a wave-like pattern simulating gait cycle data
    for (let i = 0; i < count; i++) {
      const t = (i / count) * Math.PI * 4;
      const x = (i / count) * 6 - 3;
      const y = Math.sin(t) * 1.5 + Math.cos(t * 0.5) * 0.5;
      const z = Math.cos(t) * 1.5 + Math.sin(t * 0.7) * 0.3;

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      // Color gradient from cyan to purple to pink
      const colorT = i / count;
      if (colorT < 0.33) {
        // Cyan
        colors[i * 3] = 0;
        colors[i * 3 + 1] = 0.83;
        colors[i * 3 + 2] = 1;
      } else if (colorT < 0.66) {
        // Purple
        colors[i * 3] = 0.55;
        colors[i * 3 + 1] = 0.36;
        colors[i * 3 + 2] = 0.96;
      } else {
        // Pink
        colors[i * 3] = 0.93;
        colors[i * 3 + 1] = 0.27;
        colors[i * 3 + 2] = 0.6;
      }
    }

    return { positions, colors };
  }, []);

  // Create connecting lines
  const linePositions = useMemo(() => {
    const lines: number[] = [];
    const count = 200;
    
    for (let i = 0; i < count - 1; i++) {
      const t = (i / count) * Math.PI * 4;
      const x = (i / count) * 6 - 3;
      const y = Math.sin(t) * 1.5 + Math.cos(t * 0.5) * 0.5;
      const z = Math.cos(t) * 1.5 + Math.sin(t * 0.7) * 0.3;

      const t2 = ((i + 1) / count) * Math.PI * 4;
      const x2 = ((i + 1) / count) * 6 - 3;
      const y2 = Math.sin(t2) * 1.5 + Math.cos(t2 * 0.5) * 0.5;
      const z2 = Math.cos(t2) * 1.5 + Math.sin(t2 * 0.7) * 0.3;

      lines.push(x, y, z, x2, y2, z2);
    }

    return new Float32Array(lines);
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
    if (pointsRef.current) {
      pointsRef.current.rotation.y = state.clock.elapsedTime * 0.05;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Main data points */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={positions.length / 3}
            array={positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={colors.length / 3}
            array={colors}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.08}
          vertexColors
          transparent
          opacity={0.9}
          sizeAttenuation
        />
      </points>

      {/* Connecting lines */}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={linePositions.length / 3}
            array={linePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#00d4ff" transparent opacity={0.2} />
      </lineSegments>

      {/* Grid plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]}>
        <planeGeometry args={[10, 10, 20, 20]} />
        <meshBasicMaterial color="#8b5cf6" wireframe transparent opacity={0.1} />
      </mesh>
    </group>
  );
}

function FloatingOrbs() {
  const orbs = useMemo(() => {
    return [
      { position: [-3, 1, -2] as [number, number, number], color: '#00d4ff', size: 0.15 },
      { position: [3, -1, 1] as [number, number, number], color: '#8b5cf6', size: 0.12 },
      { position: [0, 2, -1] as [number, number, number], color: '#ec4899', size: 0.1 },
      { position: [-2, -1.5, 2] as [number, number, number], color: '#00d4ff', size: 0.08 },
      { position: [2, 1.5, -2] as [number, number, number], color: '#8b5cf6', size: 0.1 },
    ];
  }, []);

  return (
    <>
      {orbs.map((orb, i) => (
        <Float key={i} speed={2} rotationIntensity={0} floatIntensity={2}>
          <mesh position={orb.position}>
            <sphereGeometry args={[orb.size, 16, 16]} />
            <meshBasicMaterial color={orb.color} transparent opacity={0.8} />
          </mesh>
        </Float>
      ))}
    </>
  );
}

export function GaitVisualization() {
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: [5, 3, 5], fov: 50 }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <DataPoints />
        <FloatingOrbs />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate
          autoRotateSpeed={0.5}
          maxPolarAngle={Math.PI / 2}
          minPolarAngle={Math.PI / 4}
        />
      </Canvas>
    </div>
  );
}
