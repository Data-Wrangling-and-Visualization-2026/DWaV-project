import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import { useStore } from '../store';
import type { DataPoint } from '../types';

interface PointProps {
  point: DataPoint;
  index: number;
  onClick: () => void;
  isSelected: boolean;
}

function Point({ point, onClick, isSelected }: PointProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  // Use happiness value for color (normalize to 0-1 range, assuming 0-10 scale)
  const colorValue = point.values.happiness / 10;
  const color = new THREE.Color().setHSL(colorValue * 0.3, 0.8, 0.5 + colorValue * 0.3);
  
  // Use trust value for size
  const scale = 0.3 + point.values.trust * 0.5;

  useFrame(() => {
    if (meshRef.current) {
      // Subtle animation
      meshRef.current.rotation.y += 0.01;
    }
  });

  return (
    <mesh
      ref={meshRef}
      position={[point.embedding.x, point.embedding.y, point.embedding.z]}
      onClick={onClick}
      onPointerOver={(e) => {
        e.stopPropagation();
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        document.body.style.cursor = 'default';
      }}
    >
      <sphereGeometry args={[scale, 16, 16]} />
      <meshStandardMaterial
        color={isSelected ? '#ff6b6b' : color}
        emissive={isSelected ? '#ff6b6b' : color}
        emissiveIntensity={isSelected ? 0.5 : 0.2}
        metalness={0.3}
        roughness={0.4}
      />
    </mesh>
  );
}

function Points() {
  const { data, selectedPoint, setSelectedPoint } = useStore();

  const handlePointClick = (point: DataPoint) => {
    setSelectedPoint(point === selectedPoint ? null : point);
  };

  return (
    <>
      {data.map((point, index) => (
        <Point
          key={`${point.country}-${point.year}-${index}`}
          point={point}
          index={index}
          onClick={() => handlePointClick(point)}
          isSelected={selectedPoint === point}
        />
      ))}
    </>
  );
}

export function Scene3D() {
  return (
    <div className="w-full h-full bg-gray-900">
      <Canvas>
        <PerspectiveCamera makeDefault position={[5, 5, 5]} fov={50} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} />
        <Points />
        <OrbitControls enableDamping dampingFactor={0.05} />
        <gridHelper args={[10, 10, '#444444', '#222222']} />
        <axesHelper args={[3]} />
      </Canvas>
    </div>
  );
}
