# Error Recovery Guide

When your automation system encounters the PyAutoGUI dependency error, follow these steps:

## 🚨 Error Symptoms
- Error message: `PyAutoGUI was unable to import pyscreeze`
- System stops working and sends Slack notification
- Cannot find buttons/images on screen

## 🔧 Quick Fix (Recommended)
Run the automated fix script:
```bash
python fix_pyautogui_dependencies.py
```

Or use the batch file (Windows):
```bash
quick_fix.bat
```

## 📱 Slack Notifications
The system will automatically send you Slack notifications when:
- ✅ Dependencies are successfully fixed
- ❌ Critical errors occur
- 🛑 System shuts down unexpectedly
- 🎉 Task processing completes

## 🔍 Manual Diagnosis
If the automatic fix doesn't work:

1. **Check Python version compatibility:**
   ```bash
   python --version
   ```
   (Should be Python 3.6+)

2. **Test PyAutoGUI manually:**
   ```bash
   python -c "import pyautogui; import pyscreeze; print('SUCCESS')"
   ```

3. **Manual dependency installation:**
   ```bash
   pip uninstall -y pyautogui pillow pyscreeze
   pip install --upgrade pip
   pip install pillow==10.4.0
   pip install pyscreeze==0.1.30
   pip install pyautogui==0.9.54
   ```

## 📋 Recovery Checklist
- [ ] Run `python fix_pyautogui_dependencies.py`
- [ ] Check Slack for fix confirmation
- [ ] Test: `python -c "import pyautogui; print('OK')"`
- [ ] Restart automation: `python task_orchestrator_enhanced.py`

## 🆘 Emergency Contacts
- Check logs: `logs/dependency_fix.log`
- Check main logs: `logs/automation_orchestrator.log`
- Slack notifications are sent to: `#automation` channel

## 🔄 System Recovery Flow
```
Error Detected → Slack Alert → Auto-Fix Attempt → Slack Update → Manual Fix (if needed) → Restart
```

## 💡 Prevention Tips
1. Always use virtual environments
2. Pin dependency versions in requirements.txt
3. Test after Python updates
4. Monitor Slack notifications
