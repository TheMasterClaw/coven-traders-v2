"use client";

import { useRef, useMemo, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Stars, OrbitControls, Text, Html } from "@react-three/drei";
import * as THREE from "three";

interface Sector {
  id: string;
  name: string;
  x: number;
  y: number;
  z: number;
  type: "core" | "outer" | "wormhole" | "black_market" | "nebula";
  yieldMultiplier: number;
  riskLevel: number;
  playerCount: number;
  isLocked: boolean;
}

const SECTOR_COLORS: Record<string, string> = {
  core: "#4ade80",
  outer: "#f97316",
  wormhole: "#a78bfa",
  black_market: "#ef4444",
  nebula: "#ec4899",
};

function SectorNode({ sector, onSelect, isSelected }: {
  sector: Sector;
  onSelect: (s: Sector) => void;
  isSelected: boolean;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.002;
      meshRef.current.rotation.x += 0.001;
    }
    if (glowRef.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.1;
      glowRef.current.scale.setScalar(scale);
    }
  });

  const color = SECTOR_COLORS[sector.type] || "#ffffff";

  return (
    <group position={[sector.x, sector.y, sector.z]}>
      {/* Glow effect */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[sector.isLocked ? 0.8 : 1.2, 16, 16]} />
        <meshBasicMaterial color={color} transparent opacity={0.15} />
      </mesh>
      
      {/* Main node */}
      <mesh
        ref={meshRef}
        onClick={() => !sector.isLocked && onSelect(sector)}
        onPointerOver={(e) => { e.stopPropagation(); document.body.style.cursor = "pointer"; }}
        onPointerOut={() => { document.body.style.cursor = "default"; }}
      >
        <icosahedronGeometry args={[sector.isLocked ? 0.4 : 0.6, 1]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isSelected ? 1.5 : 0.5}
          metalness={0.8}
          roughness={0.2}
          wireframe={sector.isLocked}
        />
      </mesh>

      {/* Label */}
      <Html distanceFactor={15} style={{ pointerEvents: "none" }}>
        <div className="text-center whitespace-nowrap">
          <div className={`text-xs font-mono font-bold ${isSelected ? "text-white" : "text-gray-400"}`}>
            {sector.name}
          </div>
          {!sector.isLocked && (
            <div className="text-[10px] text-gray-500">
              {sector.yieldMultiplier}x yield · {sector.playerCount} fleets
            </div>
          )}
          {sector.isLocked && (
            <div className="text-[10px] text-red-500">🔒 Locked</div>
          )}
        </div>
      </Html>

      {/* Risk indicator rings */}
      {sector.riskLevel > 3 && !sector.isLocked && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[1.0, 0.02, 8, 32]} />
          <meshBasicMaterial color="#ef4444" transparent opacity={0.3} />
        </mesh>
      )}
    </group>
  );
}

function ConnectionLines({ sectors }: { sectors: Sector[] }) {
  const lines = useMemo(() => {
    const connections: [THREE.Vector3, THREE.Vector3][] = [];
    for (let i = 0; i < sectors.length; i++) {
      for (let j = i + 1; j < sectors.length; j++) {
        const dist = Math.sqrt(
          Math.pow(sectors[i].x - sectors[j].x, 2) +
          Math.pow(sectors[i].y - sectors[j].y, 2) +
          Math.pow(sectors[i].z - sectors[j].z, 2)
        );
        if (dist < 8) {
          connections.push([
            new THREE.Vector3(sectors[i].x, sectors[i].y, sectors[i].z),
            new THREE.Vector3(sectors[j].x, sectors[j].y, sectors[j].z),
          ]);
        }
      }
    }
    return connections;
  }, [sectors]);

  return (
    <>
      {lines.map(([start, end], i) => (
        <line key={i}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([start.x, start.y, start.z, end.x, end.y, end.z])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#1e3a5f" transparent opacity={0.3} />
        </line>
      ))}
    </>
  );
}

function BackgroundParticles() {
  const particlesRef = useRef<THREE.Points>(null);
  const count = 1000;

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 100;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 100;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 100;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = state.clock.elapsedTime * 0.01;
    }
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.05} color="#4ade80" transparent opacity={0.6} />
    </points>
  );
}

interface SpaceMapProps {
  sectors: Sector[];
  selectedSector: string | null;
  onSelectSector: (sector: Sector) => void;
  playerFleets: { sectorId: string; count: number }[];
}

export default function SpaceMap({ sectors, selectedSector, onSelectSector, playerFleets }: SpaceMapProps) {
  return (
    <div className="w-full h-[600px] bg-black rounded-lg overflow-hidden border border-gray-800">
      <Canvas camera={{ position: [15, 10, 15], fov: 60 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#4ade80" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#a78bfa" />
        
        <Stars radius={50} depth={50} count={2000} factor={4} saturation={0} fade speed={1} />
        <BackgroundParticles />
        <ConnectionLines sectors={sectors} />
        
        {sectors.map((sector) => (
          <SectorNode
            key={sector.id}
            sector={sector}
            onSelect={onSelectSector}
            isSelected={selectedSector === sector.id}
          />
        ))}

        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={5}
          maxDistance={40}
          autoRotate
          autoRotateSpeed={0.5}
        />
      </Canvas>

      {/* HUD overlay */}
      <div className="absolute bottom-4 left-4 bg-black/80 border border-gray-700 rounded p-3 text-xs font-mono">
        <div className="text-gray-400 mb-1">SECTOR INTEL</div>
        <div className="flex gap-4">
          <span className="text-green-400">● Core Systems</span>
          <span className="text-orange-400">● Outer Rim</span>
          <span className="text-purple-400">● Wormholes</span>
          <span className="text-red-400">● Black Markets</span>
          <span className="text-pink-400">● Nebula</span>
        </div>
      </div>
    </div>
  );
}
