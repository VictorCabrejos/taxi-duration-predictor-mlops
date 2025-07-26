# 🔧 Terminal Command Best Practices for VS Code + Windows

## 🚨 **Unicode/Emoji Issues in Terminal Commands**

### **Problem:**
When using `run_in_terminal` tool with Python commands containing Unicode characters (emojis), Windows can throw:
```
UnicodeEncodeError: 'utf-8' codec can't encode character '\udfaf' in position 467: surrogates not allowed
```

### **Root Cause:**
- Windows CMD encoding (CP1252/ASCII) vs UTF-8
- VS Code terminal context vs manual terminal execution
- Long command strings with Unicode characters get corrupted

### **✅ Working Solution (Tested & Confirmed):**
```bash
# This WORKS when run manually AND takes time for heavy imports:
source activate ds_env && python -c "
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

print('[INFO] Testing bootstrap training capability...')

try:
    from taxi_duration_predictor.pipeline.train import bootstrap_training
    print('[SUCCESS] Bootstrap training module imported')
except Exception as e:
    print('[ERROR] Bootstrap training import failed:', str(e))

try:
    import mlflow
    mlflow.set_tracking_uri('sqlite:///data/mlflow.db')
    experiments = mlflow.search_experiments()
    print('[INFO] MLflow experiments found:', len(experiments))
except Exception as e:
    print('[ERROR] MLflow check failed:', str(e))

print('[INFO] Bootstrap readiness test completed')
"

# Expected output (takes 10-15 seconds):
# [INFO] Testing bootstrap training capability...
# [SUCCESS] Bootstrap training module imported
# 2025/07/25 19:56:06 INFO mlflow.store.db.utils: Creating initial MLflow database tables...
# [INFO] MLflow experiments found: 2
# [INFO] Bootstrap readiness test completed
```

### **⏰ Timing Considerations:**
- **MLflow imports**: 5-10 seconds for first database setup
- **Heavy ML libraries**: sklearn, pandas, numpy take time
- **Database operations**: MLflow database initialization is slow
- **Be patient**: Don't cancel commands too early!

### **🛠️ Copilot Tool Alternatives:**

#### **Option 1: ASCII-Safe Version**
```python
python -c "
try:
    from taxi_duration_predictor.api.main import create_app
    print('[OK] API import works')
except Exception as e:
    print('[ERROR] API import failed: ' + str(e))
"
```

#### **Option 2: Script File Approach**
```bash
# Create test_imports.py first, then:
python test_imports.py
```

#### **Option 3: Environment-Aware Testing**
```bash
# Always use conda environment activation:
source activate ds_env && python -c "import mlflow; print('[OK] MLflow ready')"
```

## 📋 **Best Practices for Copilot Instructions:**

### **1. Terminal Command Guidelines:**
- ✅ Use ASCII characters in tool commands: `[OK]`, `[ERROR]`, `[INFO]`
- ❌ Avoid emojis in `run_in_terminal` tool: `✅`, `❌`, `🎯`
- ✅ Keep commands short and focused
- ✅ Always activate conda environment: `source activate ds_env &&`

### **2. Import Testing Pattern:**
```python
# Template for testing Python imports via terminal:
source activate ds_env && python -c "
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

try:
    from taxi_duration_predictor.api.main import create_app
    print('[SUCCESS] API imports work')
except Exception as e:
    print('[ERROR] API imports failed:', str(e))
"
```

### **3. Environment Management:**
- Always prefix Python commands with conda activation
- Use absolute paths when possible
- Test environment availability before complex operations

### **4. Unicode Safety:**
```bash
# ❌ AVOID in terminal tools:
echo "✅ Success"

# ✅ USE instead:
echo "[SUCCESS] Operation completed"
```

## 🎯 **Implementation Notes:**

This was discovered during MLOps project setup where manual terminal execution worked perfectly, but automated tool execution failed due to Unicode encoding issues in Windows terminals within VS Code context.

**Key Lesson:** Manual terminal behavior ≠ Tool terminal behavior in Windows environments.
