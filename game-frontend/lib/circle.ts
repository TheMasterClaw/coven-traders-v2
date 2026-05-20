/**
 * Circle/Arc Wallet Integration
 * 
 * Uses Circle's Web3 Services (CWS) for:
 * - Embedded wallet creation
 * - USDC transactions
 * - Gasless transactions via Paymaster
 * - CCTP cross-chain transfers
 */

const CIRCLE_API_BASE = "https://api.circle.com/v1/w3s";

interface CircleConfig {
  apiKey: string;
  entitySecret: string;
  environment: "sandbox" | "production";
}

interface Wallet {
  id: string;
  address: string;
  blockchain: string;
  createDate: string;
}

export class CircleWalletClient {
  private apiKey: string;
  private entitySecret: string;
  private baseUrl: string;

  constructor(config: CircleConfig) {
    this.apiKey = config.apiKey;
    this.entitySecret = config.entitySecret;
    this.baseUrl = config.environment === "production" 
      ? CIRCLE_API_BASE 
      : "https://api-sandbox.circle.com/v1/w3s";
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
      throw new Error(`Circle API error: ${res.status} ${await res.text()}`);
    }
    return res.json();
  }

  async createWallet(userId: string): Promise<Wallet> {
    const res = await this.request("/wallets", {
      method: "POST",
      body: JSON.stringify({
        idempotencyKey: crypto.randomUUID(),
        accountType: "SCA",
        blockchains: ["ARC-TESTNET"], // or ARC-MAINNET
        metadata: { userId },
      }),
    });
    return res.data.wallet;
  }

  async getWallet(walletId: string): Promise<Wallet> {
    const res = await this.request(`/wallets/${walletId}`);
    return res.data.wallet;
  }

  async getBalance(walletId: string, token: string = "USDC"): Promise<string> {
    const res = await this.request(`/wallets/${walletId}/balances`);
    const balance = res.data.tokenBalances.find((b: any) => b.token.symbol === token);
    return balance?.amount || "0";
  }

  async transferUSDC(
    walletId: string,
    toAddress: string,
    amount: string,
    paymaster?: boolean
  ): Promise<string> {
    const tx = await this.request("/transactions/transfer", {
      method: "POST",
      body: JSON.stringify({
        idempotencyKey: crypto.randomUUID(),
        walletId,
        tokenId: "USDC",
        destinationAddress: toAddress,
        amounts: [amount],
        fee: paymaster ? { type: "level" } : undefined,
      }),
    });
    return tx.data.id;
  }

  async enterCrusade(walletId: string, crusadeId: number, entryFee: string): Promise<string> {
    // This would call the CrusadeEscrow contract
    // Using Circle's smart contract execution
    const contractAddress = process.env.CRUSADE_ESCROW_ADDRESS;
    const tx = await this.request("/transactions/contractExecution", {
      method: "POST",
      body: JSON.stringify({
        idempotencyKey: crypto.randomUUID(),
        walletId,
        contractAddress,
        abiFunctionSignature: "enterCrusade(uint256)",
        abiParameters: [crusadeId.toString()],
        fee: { type: "level" }, // gasless via Paymaster
      }),
    });
    return tx.data.id;
  }
}

export default CircleWalletClient;
