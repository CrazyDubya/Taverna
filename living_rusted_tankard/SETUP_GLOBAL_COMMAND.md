# Setup Global AI Observer Command

## 🚀 Quick Setup (Choose One Option)

### Option 1: Direct Full Path (Works Immediately)
```bash
# Run from anywhere using full path
/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard/ai-observer-global.sh --demo

# Or with any options
/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard/ai-observer-global.sh --new --personality "social_butterfly"
```

### Option 2: Add to PATH (Run Once)
```bash
# Add to your shell profile (choose your shell)
echo 'export PATH="$PATH:/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard"' >> ~/.zshrc
source ~/.zshrc

# Then run from anywhere
ai-observer-global.sh --demo
```

### Option 3: Create Alias (Run Once)
```bash
# Add alias to your shell profile
echo 'alias ai-observer="/Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard/ai-observer-global.sh"' >> ~/.zshrc
source ~/.zshrc

# Then run from anywhere
ai-observer --demo
```

### Option 4: Manual Symlink (If you have admin access)
```bash
# Create symlink in /usr/local/bin
sudo ln -sf /Users/pup/ClaudeWorkshop/Taverna/living_rusted_tankard/ai-observer-global.sh /usr/local/bin/ai-observer

# Then run from anywhere
ai-observer --demo
```

## 📋 Available Commands

Once set up, run from any directory:

```bash
# Start simple demo
ai-observer --demo

# Start new AI session  
ai-observer --new

# Different personalities
ai-observer --new --personality "curious_explorer"
ai-observer --new --personality "cautious_merchant" 
ai-observer --new --personality "social_butterfly"
ai-observer --new --personality "mysterious_wanderer"

# Custom AI name
ai-observer --new --name "MyAI" --personality "curious_explorer"

# Web interface (if working)
ai-observer --web

# List available personalities
ai-observer --list-personalities
```

## ✅ Test Your Setup

After setting up, test from any directory:
```bash
cd ~
ai-observer --demo
```

If it works, you'll see:
```
🎮 Running Simple AI Demo
========================================
🤖 Created AI: DemoGemma
🎭 Personality: curious_explorer
```