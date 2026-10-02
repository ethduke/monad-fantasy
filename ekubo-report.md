# Ekubo holdings check — INCOMPLETE (no data retrieved)

**Address (Starknet mainnet):** `0x029ec70F2Ad799887e1936f9A7A5f2f08378A4EB77Aec8FBE0cAF0B0981543B0`
**Attempted:** 2026-10-02T19:39:03Z

## Summary
Funds left in Ekubo: **UNKNOWN**. Could not be determined.
Total est. value: **not available**. No prices or balances were retrieved.

This does **not** mean the address is empty. Every data source needed for this check (Ekubo MCP, the Ekubo API, Ekubo docs, public Starknet RPCs, and block explorers) is blocked by this cloud session's network egress policy, so no read succeeded. No amounts appear below because no source returned any.

## Liquidity positions
| NFT ID | Pair | Fee tier | Range | In range? | Token0 amt | Token1 amt | Unclaimed fees | USD |
|---|---|---|---|---|---|---|---|---|
| Not checked: source unreachable | | | | | | | | |

## Open orders (limit / TWAMM)
| Order ID | Type | Sell → Buy | Remaining | Proceeds to withdraw | USD |
|---|---|---|---|---|---|
| Not checked: source unreachable | | | | | |

## Claimable rewards
| Source | Token | Amount | USD | Claim deadline (if any) |
|---|---|---|---|---|
| Ekubo rewards / incentives: not checked | | | | |
| Airdrop / recovery-fund claims: not checked | | | | |
| ve(3,3) / STONX allocations: not checked | | | | |

## Empty / closed positions
Not checked. The Positions NFT list could not be read, so empty NFTs cannot be told apart from missing ones.

## Sources & method
None of Options A, B, or C succeeded. Each one was blocked at the network layer, before any request reached Ekubo or Starknet.

| Option | Target | Result |
|---|---|---|
| A: Ekubo MCP | `https://mcp.ekubo.org/mcp` | Proxy CONNECT rejected (403, organization egress policy). `claude mcp add` was not run because the host is unreachable. |
| B: HTTP API | `https://docs.ekubo.org/openapi/ekubo.json` | Blocked (container proxy and WebFetch both returned `EGRESS_BLOCKED`) |
| B: HTTP API | `https://prod-api.ekubo.org/positions/<address>?chainId=23448594291968334` | Blocked (403 from container, `EGRESS_BLOCKED` via WebFetch) |
| C: Contract addresses | `https://docs.ekubo.org/reference/contracts/` | Blocked (same host as above), so Core/Positions/NFT addresses could not be confirmed |
| C: Starknet RPC | `starknet-mainnet.public.blastapi.io`, `free-rpc.nethermind.io`, `starknet.drpc.org`, `rpc.starknet.lava.build`, `api.cartridge.gg`, `starknet-mainnet.g.alchemy.com` | All blocked (proxy CONNECT rejected) |
| C: Explorers | `voyager.online`, `api.voyager.online`, `starkscan.co`, `api.starkscan.co` | All blocked (container and WebFetch) |

Reachable hosts were only GitHub, PyPI, and npm, and none of them serves live Starknet or Ekubo state.

No transactions were built, signed, or sent. No keys were requested or used.

## To complete this check
Allow these hosts in the cloud environment's **Network access** settings (environment menu in the session title bar → Edit), or switch to a broader access level, then rerun:

- `mcp.ekubo.org` (Option A, preferred)
- `prod-api.ekubo.org` and `docs.ekubo.org` (Option B, plus contract addresses for C)
- One Starknet RPC, for example `starknet-mainnet.public.blastapi.io` or `rpc.starknet.lava.build` (Option C)
- Optional: `voyager.online` / `api.voyager.online` for interaction history

You can also run the check yourself from any unrestricted machine. In the Claude Code CLI:
```bash
claude mcp add --transport http ekubo https://mcp.ekubo.org/mcp
```
Then ask for positions, rewards, and STONX/ve allocations for the address above. Or open the Ekubo app's positions page while connected with this address in read-only view.
