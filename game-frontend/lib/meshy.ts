/**
 * Meshy.ai API Client for 3D Asset Generation
 * 
 * Endpoints:
 * - POST /v2/text-to-3d → Generate 3D model from text
 * - GET /v2/text-to-3d/{task_id} → Check generation status
 * - POST /v2/image-to-3d → Generate from image
 * - POST /v2/text-to-texture → Generate texture for existing model
 */

const MESHY_API_BASE = "https://api.meshy.ai/v2";

interface MeshyConfig {
  apiKey: string;
  baseUrl?: string;
}

interface TextTo3DRequest {
  mode: "preview" | "refine";
  prompt: string;
  art_style: "realistic" | "cartoon" | "low-poly" | "sci-fi" | "cyberpunk";
  negative_prompt?: string;
  resolution: "256" | "512" | "1024";
  enable_pbr: boolean;
}

interface MeshyTask {
  id: string;
  status: "PENDING" | "IN_PROGRESS" | "SUCCEEDED" | "FAILED";
  model_url?: string;
  thumbnail_url?: string;
  video_url?: string;
  progress?: number;
  error?: string;
}

export class MeshyClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(config: MeshyConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || MESHY_API_BASE;
  }

  private async request(path: string, options: RequestInit = {}): Promise<any> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
    if (!res.ok) {
      throw new Error(`Meshy API error: ${res.status} ${await res.text()}`);
    }
    return res.json();
  }

  async generateTextTo3D(params: TextTo3DRequest): Promise<MeshyTask> {
    return this.request("/text-to-3d", {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  async getTask(taskId: string): Promise<MeshyTask> {
    return this.request(`/text-to-3d/${taskId}`);
  }

  async pollUntilComplete(taskId: string, intervalMs = 5000, timeoutMs = 300000): Promise<MeshyTask> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const task = await this.getTask(taskId);
      if (task.status === "SUCCEEDED" || task.status === "FAILED") {
        return task;
      }
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    throw new Error("Meshy generation timed out");
  }

  // Preset generators for game assets
  async generateDiscipleAvatar(specialization: string, tier: string): Promise<MeshyTask> {
    const prompts: Record<string, string> = {
      perp_warrior: `A fearsome space fleet commander with kinetic weapon implants, holographic leverage displays floating around them, dark metallic armor with glowing red accents, sci-fi universe, dramatic lighting`,
      oracle_seer: `A mystical AI entity with crystalline sensor arrays, probability streams visualized as light threads, ethereal blue glow, floating in a nebula, sci-fi fantasy`,
      market_maker: `A massive orbital trade station with automated drone arms, liquidity pools visualized as glowing orbs, industrial sci-fi aesthetic, golden accents`,
      treasurer: `A fortress vault ship with reinforced shields, yield beams connecting to distant stars, regal purple and gold, imposing presence`,
      arbitrageur: `A sleek warp-drive interceptor with dual-portal generators, streaks of light from rapid jumps, silver and cyan, agile posture`,
      signal_hunter: `A deep-space probe with massive antenna arrays, signal waves emanating outward, dark stealth coating with neon green highlights`,
    };

    const prompt = prompts[specialization] || prompts.perp_warrior;
    
    return this.generateTextTo3D({
      mode: "preview",
      prompt: `${prompt}, ${tier} quality, highly detailed, game asset`,
      art_style: "sci-fi",
      resolution: "512",
      enable_pbr: true,
    });
  }

  async generateCommandCenter(level: number): Promise<MeshyTask> {
    return this.generateTextTo3D({
      mode: "preview",
      prompt: `A massive space command center station, level ${level}, holographic star maps, drone fleet docking bays, glowing control panels, sci-fi universe, cinematic`,
      art_style: "sci-fi",
      resolution: "512",
      enable_pbr: true,
    });
  }

  async generateSectorEnvironment(sectorType: string): Promise<MeshyTask> {
    const prompts: Record<string, string> = {
      core_systems: "A stable, well-lit star system with orderly orbital lanes, safe zone markers, corporate stations, clean and organized",
      outer_rim: "A chaotic asteroid belt with volatile energy storms, abandoned ships, danger signs, gritty and dangerous",
      wormhole: "A swirling vortex of spacetime with bridge structures, cross-dimensional energy, mysterious and powerful",
      black_market: "A hidden shadow station in a dark nebula, illegal trade markers, cloaked ships, ominous red lighting",
      nebula: "A colorful gas cloud with floating resource extractors, yield beams, mystical and profitable",
    };

    return this.generateTextTo3D({
      mode: "preview",
      prompt: `${prompts[sectorType] || prompts.core_systems}, environment scene, game background, highly detailed`,
      art_style: "sci-fi",
      resolution: "512",
      enable_pbr: true,
    });
  }
}

export default MeshyClient;
