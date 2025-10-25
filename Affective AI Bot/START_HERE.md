# 🚀 Quick Start - Run Your Project

## 3 Easy Ways to Run AffectiveCore

---

### **Method 1: Python Script (Recommended) 🌟**

**Opens browser automatically!**

```bash
cd "/Users/DK19/Downloads/Affective AI Bot"
source venv/bin/activate
python run.py
```

**What happens:**
- ✅ Displays clickable links in terminal
- ✅ Opens browser automatically
- ✅ Shows helpful tips
- ✅ Clean shutdown with Ctrl+C

---

### **Method 2: Bash Script**

```bash
cd "/Users/DK19/Downloads/Affective AI Bot"
./run.sh
```

**What happens:**
- ✅ Displays clickable links
- ✅ Activates virtual environment
- ✅ Starts dashboard
- ✅ Clean terminal output

---

### **Method 3: Direct Command**

```bash
cd "/Users/DK19/Downloads/Affective AI Bot"
source venv/bin/activate
streamlit run app.py --server.port 8501
```

**What happens:**
- ✅ Streamlit shows its own clickable links
- ✅ Most control over startup
- ✅ Traditional method

---

## 🌐 Accessing the Dashboard

Once started, you'll see clickable links in the terminal:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.0.116:8501
```

**In most terminals:**
- **Cmd+Click** (Mac) or **Ctrl+Click** (Windows/Linux) opens the link
- Or **copy-paste** the URL into your browser

---

## 🛑 How to Stop

Press **Ctrl+C** in the terminal

---

## 💡 Pro Tips

### **Make it Even Easier:**

**Create a desktop shortcut:**

1. Open Terminal
2. Run:
```bash
cat > ~/Desktop/AffectiveCore.command << 'EOF'
#!/bin/bash
cd "/Users/DK19/Downloads/Affective AI Bot"
source venv/bin/activate
python run.py
EOF
chmod +x ~/Desktop/AffectiveCore.command
```

3. Now **double-click** `AffectiveCore.command` on your desktop!

---

### **For Demo/Hackathon:**

1. **Before presenting:**
   ```bash
   cd "/Users/DK19/Downloads/Affective AI Bot"
   source venv/bin/activate
   python run.py
   ```

2. **Wait for browser to open** (2-3 seconds)

3. **Show the dashboard** to judges

4. **Upload audio** and analyze emotions

5. **Show results** in real-time

---

## 📊 What You'll See

When the dashboard opens:

```
╔════════════════════════════════════════════════════════════╗
║     🎭 AffectiveCore: Speech Emotion Detection 🎭        ║
╚════════════════════════════════════════════════════════════╝

Multimodal emotion analysis from speech audio

📁 File Analysis | 📊 Batch Analysis | 📈 Statistics

Upload Audio File
[Drag and drop or click to browse]
```

---

## ✅ Verify It's Working

1. Dashboard opens in browser
2. You see "Pipeline loaded" (green) in sidebar
3. You can upload audio files
4. Results appear in <2 seconds

---

## 🔧 Troubleshooting

### **Terminal Links Not Clickable?**

**iTerm2 (Mac):**
- Cmd+Click should work
- Or: iTerm2 → Preferences → Profiles → Advanced → Enable "Semantic History"

**VS Code Terminal:**
- Cmd+Click should work
- Or: Copy-paste the URL

**Default Terminal:**
- Copy-paste the URL
- Or use the Python script (`python run.py`) which auto-opens browser

### **Port 8501 Already in Use?**

```bash
# Kill existing processes
pkill -f "streamlit run app.py"

# Or use a different port
streamlit run app.py --server.port 8502
```

### **Can't Find Python?**

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Should see (venv) in your prompt
```

---

## 🎯 For Your Hackathon Demo

**Best approach:**

1. **Open two terminals side-by-side:**
   - Terminal 1: Run `python run.py`
   - Terminal 2: Keep for showing code

2. **Browser window:**
   - Full screen the dashboard
   - Have test audio file ready

3. **Demo flow:**
   - "Let me show you AffectiveCore in action"
   - Upload audio file
   - Point to results as they appear
   - Show emotion breakdown charts
   - Highlight the speed (<2 seconds)

---

## 📚 More Resources

- **Full Documentation:** README.md
- **Presentation Guide:** HACKATHON_PRESENTATION.md
- **Code Overview:** CODE_FLOW_DIAGRAM.txt
- **Quick Reference:** See terminal output above

---

## 🎉 You're All Set!

Your AffectiveCore system is ready to demo!

**Quick command to remember:**
```bash
python run.py
```

That's it! 🚀

