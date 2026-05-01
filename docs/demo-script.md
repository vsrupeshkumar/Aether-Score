# Demo Video Script

## Duration: 3-5 minutes

**Total Target Time:** 4 minutes (240 seconds)

---

### 1. Hook (10-15 seconds) â±ï¸

**Script:**
"On most blockchains, lending is blind. There's no portable on-chain credit identity. AETHER-SCORE fixes that for QIE."

**Visual:**
- Show AETHER-SCORE logo/title
- Quick text overlay: "AI Credit Passport on QIE"

**Timing:** 10-15 seconds

---

### 2. Problem Statement (30 seconds) â±ï¸

**Script:**
"Today's DeFi lending protocols face a major challenge:
- Most loans are over-collateralized, making them capital inefficient
- There's no way to assess borrower risk on-chain
- Each protocol has to build its own risk assessment from scratch
- New chains like QIE need better tools for safe DeFi adoption"

**Visual:**
- Show problem statement slides or text
- Highlight pain points

**Timing:** 30 seconds

---

### 3. Solution Overview (30-45 seconds) â±ï¸

**Script:**
"AETHER-SCORE solves this with an AI-powered credit passport:
- Wallets get a reusable credit score from 0 to 1000
- The score is stored as a soulbound NFT on QIE
- Any DeFi app can query the score with a single contract call
- Scores are calculated using AI analysis of on-chain activity"

**Visual:**
- Show solution diagram
- Highlight: AI â†’ Score â†’ NFT â†’ DeFi Integration

**Timing:** 30-45 seconds

---

### 4. Architecture (30 seconds) â±ï¸

**Script:**
"Here's how AETHER-SCORE works:
- Frontend connects wallets and displays scores
- Backend runs our AI scoring algorithm
- Smart contracts on QIE store scores as soulbound NFTs
- QIE Oracles provide price data for risk assessment"

**Visual:**
- Show architecture diagram:
  ```
  Frontend (Next.js) â†’ Backend (FastAPI) â†’ QIE Blockchain (Contracts)
         â†“                    â†“                      â†“
    Wallet Connect      AI Scoring          Soulbound NFT
  ```
- Or use a simple diagram slide

**Timing:** 30 seconds

---

### 5. Live Demo (2-3 minutes) â±ï¸ **CRITICAL SECTION**

**Step 1: Connect Wallet (15-20s)**
- "Let me connect my QIE wallet"
- Show wallet connection button
- Click "Connect Wallet"
- MetaMask/QIE Wallet popup appears
- User confirms connection
- Display connected address (e.g., "0x1234...5678")
- Show wallet balance (e.g., "0.5 QIE")
- **MUST SHOW:** Balance display and address

**Step 2: Generate Score (30-40s)**
- "Now I'll generate my credit passport"
- Click "Generate My Credit Passport" button
- Show loading state: "Generating Score..."
- Explain: "Our AI is analyzing my wallet history, transaction patterns, and portfolio composition using QIE Oracles for price data"
- Wait for backend to compute score
- Wait for on-chain transaction

**Step 3: View Results (20-30s)**
- Show score gauge (e.g., 750/1000)
- Highlight the score number
- Show risk band badge (Low/Medium/High)
- Read explanation: "Low risk: High transaction activity, good volume, stable portfolio"
- **MUST SHOW:** Score, risk band, and explanation clearly

**Step 4: On-Chain Verification (30-40s)** âš ï¸ **CRITICAL**
- "The score is now stored on-chain as a soulbound NFT"
- Show transaction hash displayed on screen
- **MUST CLICK:** Link to QIE Explorer
- Show explorer page with transaction details
- Point out: "Transaction successful"
- Show contract address
- Show event logs (PassportMinted or ScoreUpdated)
- Explain: "Notice this is a soulbound NFT - it can't be transferred, ensuring score integrity"
- **MUST SHOW:** Explorer link working and transaction visible

**Step 5: Integration Demo (20-30s)**
- Switch to dev/integration page (or show code)
- "Any DeFi protocol can integrate AETHER-SCORE in just a few lines"
- Show code snippet:
  ```solidity
  IAETHER-SCOREScore.ScoreView memory sv = neuro.getScore(user);
  if (sv.riskBand == 1) {
      ltv = 80%; // Low risk
  }
  ```
- Explain: "They can adjust loan-to-value ratios, interest rates, or collateral requirements based on the credit score"
- **MUST SHOW:** Code snippet clearly readable

**Total Demo Time:** 2-3 minutes (120-180 seconds)

### 6. Technical Deep Dive (30-45 seconds) â±ï¸

**Script:**
"Under the hood:
- Smart contracts deployed on QIE Testnet
- FastAPI backend with AI scoring algorithm
- Feature extraction from wallet history
- Integration with QIE Oracles for price data
- QIEDex integration ready for NCRD token creation
- Comprehensive contract tests ensure reliability"

**Visual:**
- Show code snippets or architecture
- Highlight QIE ecosystem features used

**Timing:** 30-45 seconds

---

### 7. Developer Integration (20-30 seconds) â±ï¸

**Script:**
"Here's how easy it is for any DeFi protocol to integrate AETHER-SCORE..."

**Visual:**
- Show integration code again (if not shown in Step 5)
- Show the `getScore()` function call
- Explain use cases: LTV adjustment, interest rates, collateral requirements

**Timing:** 20-30 seconds

---

### 8. Vision & Impact (20-30 seconds) â±ï¸

**Script:**
"AETHER-SCORE's vision:
- Become the default risk layer for all QIE DeFi protocols
- Enable under-collateralized lending
- Expand to real-world credit and payroll
- Open SDK for easy integration

Our impact: We enable safe, capital-efficient lending across the entire QIE ecosystem."

**Visual:**
- Show impact statement
- Highlight ecosystem benefits

**Timing:** 20-30 seconds

---

### 9. Closing (10 seconds) â±ï¸

**Script:**
"AETHER-SCORE: Making DeFi safer, one credit score at a time. Built for QIE Hackathon 2025."

**Visual:**
- Show AETHER-SCORE logo
- "Thank you for watching"

**Timing:** 10 seconds

---

## â±ï¸ Total Timing Breakdown

| Section | Time | Cumulative |
|---------|------|------------|
| Hook | 10-15s | 15s |
| Problem | 30s | 45s |
| Solution | 30-45s | 90s |
| Architecture | 30s | 120s |
| Live Demo | 120-180s | 300s (5 min) |
| Technical | 30-45s | 345s |
| Integration | 20-30s | 375s |
| Vision | 20-30s | 405s |
| Closing | 10s | 415s |

**Target Total:** 4-5 minutes (240-300 seconds)

---

## âœ… Key Points to Emphasize (MUST SHOW)

### Critical for $500 Requirements:
- âœ… Wallet integration working (connect, balance, address)
- âœ… Real on-chain transactions (tx hash visible)
- âœ… Explorer link working (transaction verified on-chain)

### For Main Prize Competition:
- âœ… AI-powered scoring (explain algorithm)
- âœ… Easy integration for other dApps (show code)
- âœ… QIE ecosystem features used (Oracles, QIEDex)
- âœ… Soulbound NFT concept (non-transferable)

## ðŸŽ¬ Tips for Recording

### Technical Setup:
- Use screen recording software (OBS, QuickTime, Loom)
- Record in 1080p minimum
- Use clear, readable fonts in code snippets
- Ensure good audio quality (external mic recommended)

### Recording Best Practices:
- Show clear transitions between steps
- Highlight transaction hashes and explorer links
- Keep code snippets readable (zoom if needed)
- Pause briefly after important actions
- Speak clearly and at moderate pace
- Show mouse cursor movements for clarity

### What to Avoid:
- âŒ Rushing through steps
- âŒ Unclear audio
- âŒ Small text that's hard to read
- âŒ Skipping the explorer verification
- âŒ Not showing the transaction hash

### Post-Production:
- Add text overlays for key points
- Add timestamps if helpful
- Ensure video is under 5 minutes
- Test video playback before uploading

## ðŸ“‹ Pre-Recording Checklist

- [ ] Contracts deployed to QIE Testnet
- [ ] Backend running and accessible
- [ ] Frontend running and accessible
- [ ] Wallet has testnet tokens
- [ ] Test the full flow before recording
- [ ] Explorer link works
- [ ] All screenshots ready
- [ ] Script reviewed and practiced

## ðŸŽ¯ Demo Flow Summary

1. **Hook** (15s) - Problem statement
2. **Solution** (45s) - What AETHER-SCORE does
3. **Architecture** (30s) - How it works
4. **Live Demo** (180s) - **MOST IMPORTANT**
   - Connect wallet âœ…
   - Generate score âœ…
   - Show results âœ…
   - Verify on explorer âœ…
   - Show integration code âœ…
5. **Technical** (45s) - Deep dive
6. **Integration** (30s) - Developer view
7. **Vision** (30s) - Impact
8. **Closing** (10s) - Wrap up

**Total: ~4-5 minutes**


