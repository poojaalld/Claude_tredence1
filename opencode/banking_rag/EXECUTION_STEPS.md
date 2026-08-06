# Enterprise Banking RAG Assistant - Execution Steps

## Complete Step-by-Step Guide to Run the Project

---

## **PHASE 1: ENVIRONMENT SETUP (10 minutes)**

### **Step 1.1: Navigate to Project Directory**
```bash
cd C:\Users\pooja\Claude_tredence\opencode\banking_rag
```

### **Step 1.2: Create Python Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

**Verify activation:**
```bash
# You should see (venv) in your terminal prompt
```

### **Step 1.3: Upgrade pip**
```bash
python -m pip install --upgrade pip
```

### **Step 1.4: Install All Dependencies**
```bash
pip install -r part_1_environment/requirements.txt
```

**This will install:**
- langchain, langchain-community, langchain-openai
- pydantic, python-dotenv
- faiss-cpu (for vector indexing)
- fastapi, uvicorn (for API)
- streamlit (for UI)
- anthropic (for Claude)
- pytest (for testing)
- And all other required packages

**Wait for installation to complete** (may take 2-5 minutes)

### **Step 1.5: Verify Installation**
```bash
# Check Python version (should be 3.13+)
python --version

# Verify key packages are installed
python -c "import faiss; import fastapi; import streamlit; print('✓ All packages installed successfully')"
```

---

## **PHASE 2: CONFIGURATION (5 minutes)**

### **Step 2.1: Copy Environment Template**
```bash
copy part_1_environment\.env.example .env
```

### **Step 2.2: Edit Configuration File**
Open `.env` file and configure (or leave defaults for demo):

```env
# Optional: Add your API keys for production use
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# VOYAGE_API_KEY=pa-...

# Default settings (good for testing)
APP_ENV=development
LOG_LEVEL=INFO
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
CHUNK_SIZE=1024
TOP_K_RETRIEVAL=5
EMBEDDING_MODEL=voyage-3
CHAT_MODEL=claude-3-sonnet-20240229
```

**Save the file.**

---

## **PHASE 3: TESTING (10 minutes)**

### **Step 3.1: Run All Tests**
```bash
# Run all tests across all parts
pytest part_*/test_*.py -v
```

**Expected output:**
```
130+ tests PASSED ✓
```

### **Step 3.2: Run Tests by Part (Optional)**
```bash
# Test Part 1: Environment
pytest part_1_environment/test_config.py -v

# Test Part 2: Document Loader
pytest part_2_document_loader/test_document_loader.py -v

# Test Part 3: Semantic Chunking
pytest part_3_semantic_chunking/test_semantic_chunker.py -v

# Test Part 4: Embeddings
pytest part_4_embeddings/test_embedding_generator.py -v

# Test Part 5: Indexing
pytest part_5_indexing/test_vector_indexing.py -v

# Test Part 6: Retriever
pytest part_6_retriever/test_retriever.py -v

# Test Part 7: RAG Pipeline
pytest part_7_rag_pipeline/test_rag_pipeline.py -v
```

### **Step 3.3: Check Logs**
```bash
# Verify logs directory exists
dir logs/

# View application log (if any tests ran logging)
type logs\app.log
```

---

## **PHASE 4: START THE BACKEND API (10 minutes)**

### **Step 4.1: Start FastAPI Server**
```bash
python -m uvicorn part_8_backend.app:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### **Step 4.2: Verify API Health (New Terminal)**
```bash
# Open a NEW terminal/PowerShell window (keep the API running)
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-08-05T...",
  "version": "1.0.0"
}
```

### **Step 4.3: Access API Documentation**
Open your browser and visit:
```
http://localhost:8000/docs
```

You should see interactive Swagger UI with all endpoints documented.

---

## **PHASE 5: START THE FRONTEND UI (5 minutes)**

### **Step 5.1: Open Another Terminal**
Open a **third terminal** window and activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### **Step 5.2: Start Streamlit App**
```bash
streamlit run part_9_frontend/app.py
```

**Expected output:**
```
Welcome to Streamlit! 🎈

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### **Step 5.3: Open Frontend in Browser**
Streamlit should automatically open. If not, visit:
```
http://localhost:8501
```

---

## **PHASE 6: TEST THE SYSTEM (15 minutes)**

### **Step 6.1: Test via Streamlit UI (Recommended)**

**In the Streamlit browser tab:**

1. **Check "Configuration" in sidebar**
   - Verify API URL is `http://localhost:8000`
   - You can adjust retrieval settings (top_k, max_tokens)

2. **Ask a Question**
   - Type in the chat input: "What is the interest rate for savings accounts?"
   - Press Enter or click Send

3. **View Results**
   - See the AI-generated answer
   - Click "View Details" to see:
     - Confidence score
     - Processing time
     - Number of chunks retrieved
     - Source documents

4. **Try More Questions**
   ```
   - "How much does a personal loan cost?"
   - "What are the ATM withdrawal fees?"
   - "How do I apply for a mortgage?"
   - "What is your fraud protection policy?"
   ```

5. **Check Statistics Tab**
   - Click "Statistics" tab
   - Click "Refresh Statistics"
   - View system metrics:
     - Total queries processed
     - Average processing time
     - Total chunks retrieved
     - Average confidence score

6. **View About Tab**
   - Information about the system
   - Example questions (click to auto-fill)
   - Technology stack details

### **Step 6.2: Test via REST API (Advanced)**

**In a new terminal:**

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: Process a query
curl -X POST http://localhost:8000/query `
  -H "Content-Type: application/json" `
  -d '{
    "query": "What is the interest rate for savings accounts?",
    "top_k": 5,
    "max_tokens": 2048
  }'

# Test 3: Get statistics
curl http://localhost:8000/stats
```

**Expected JSON responses with answers and metadata.**

### **Step 6.3: Test via Python Code (Development)**

**In a new Python script:**

```python
import requests

# Query the API
response = requests.post(
    'http://localhost:8000/query',
    json={
        'query': 'What are the fees for wire transfers?',
        'top_k': 5,
        'max_tokens': 2048
    }
)

# Print results
result = response.json()
print(f"Question: {result['query']}")
print(f"Answer: {result['response']}")
print(f"Sources: {result['sources']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Processing time: {result['processing_time']:.2f}s")
```

---

## **PHASE 7: MONITOR AND DEBUG (5 minutes)**

### **Step 7.1: Check API Logs**
In the **API terminal**, you'll see logs like:
```
INFO:     Processing query: What is interest rate?
INFO:     Query processed in 2.345s. Retrieved 5 chunks from 1 sources.
```

### **Step 7.2: Check Frontend Logs**
In the **Streamlit terminal**, you'll see:
```
2026-08-05 10:30:45.123 Querying RAG API...
2026-08-05 10:30:47.456 Response received successfully
```

### **Step 7.3: View Application Logs**
```bash
# Check log files
type logs\app.log
type logs\error.log
```

### **Step 7.4: Troubleshoot Connection Issues**
```bash
# If API won't start, check port 8000
netstat -ano | findstr :8000

# If Streamlit won't connect to API
# 1. Verify API is running (check API terminal)
# 2. Update API URL in Streamlit sidebar
# 3. Check .env file configuration
```

---

## **PHASE 8: RUN EXAMPLE WORKFLOWS (20 minutes)**

### **Workflow 1: Single Query**
1. Start in Streamlit UI
2. Ask: "What is the interest rate for savings accounts?"
3. View the complete response with sources
4. Note confidence score and processing time

### **Workflow 2: Multi-Turn Conversation**
1. Ask first question: "What account types do you offer?"
2. Follow-up: "What is the interest rate for savings?"
3. Another: "Are there any fees?"
4. Note conversation history grows in chat

### **Workflow 3: API Integration**
1. Write a Python script to query the API
2. Process multiple queries
3. Aggregate results
4. Export data

### **Workflow 4: Performance Testing**
1. Run 10 queries in sequence
2. Note response times
3. Check statistics for average metrics
4. Verify system handles multiple queries

---

## **PHASE 9: LOAD CUSTOM DATA (Optional, 10 minutes)**

### **Step 9.1: Add Your Documents**
```bash
# Copy your documents to data folder
copy your_banking_docs.txt data/
copy your_policies.pdf data/
copy your_procedures.docx data/
```

### **Step 9.2: Reinitialize the System**
```bash
# Restart API server (in API terminal, press Ctrl+C)
python -m uvicorn part_8_backend.app:app --reload

# Restart Streamlit (in Streamlit terminal, press Ctrl+C)
streamlit run part_9_frontend/app.py
```

### **Step 9.3: Test with New Data**
- Ask questions about your new documents
- Verify retrieval works with custom data

---

## **PHASE 10: CLEAN SHUTDOWN (2 minutes)**

### **Step 10.1: Stop Services Gracefully**
```bash
# In API terminal: Press Ctrl+C
# In Streamlit terminal: Press Ctrl+C
# In test terminal: Close the window

# Deactivate virtual environment
deactivate
```

### **Step 10.2: Verify Shutdown**
```bash
# Verify ports are freed
netstat -ano | findstr :8000
# Should show no results
```

---

## **QUICK REFERENCE: Terminal Commands**

### **All-in-One Setup**
```bash
# Navigate to project
cd banking_rag

# Setup
python -m venv venv
venv\Scripts\activate
pip install -r part_1_environment/requirements.txt
copy part_1_environment\.env.example .env

# Run tests
pytest part_*/test_*.py -v

# Start API (in terminal 1)
python -m uvicorn part_8_backend.app:app --reload

# Start Frontend (in terminal 2)
streamlit run part_9_frontend/app.py

# Test API (in terminal 3)
curl http://localhost:8000/health
```

---

## **TROUBLESHOOTING GUIDE**

### **Issue: "Module not found" errors**
```bash
# Solution: Reinstall dependencies
pip install --upgrade -r part_1_environment/requirements.txt
```

### **Issue: Port 8000 already in use**
```bash
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with the process ID)
taskkill /PID <PID> /F

# Or use different port
python -m uvicorn part_8_backend.app:app --port 8001
```

### **Issue: API won't start**
```bash
# Check logs
type logs\error.log

# Verify Python version
python --version  # Should be 3.13+

# Test imports
python -c "import fastapi; import pydantic; print('OK')"
```

### **Issue: Streamlit can't connect to API**
1. Verify API is running (check API terminal)
2. Check API URL in Streamlit sidebar
3. Try: `curl http://localhost:8000/health`
4. If failing, restart both services

### **Issue: Tests failing**
```bash
# Run single test to see detailed error
pytest part_1_environment/test_config.py::TestConfiguration::test_settings_initialization -v

# Check logs
type logs\app.log
```

---

## **VERIFICATION CHECKLIST**

- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] Configuration file (.env) created
- [ ] All tests passing (130+/130+)
- [ ] API server running on port 8000
- [ ] API health check responds
- [ ] Streamlit UI loads at localhost:8501
- [ ] Can submit queries through UI
- [ ] Receive answers with confidence scores
- [ ] Statistics tab shows metrics
- [ ] Example questions work
- [ ] Can see source documents

---

## **EXPECTED RESULTS**

### **API Response Example**
```json
{
  "query": "What is the interest rate for savings accounts?",
  "response": "The interest rate for savings accounts is 2.5% APY...",
  "sources": ["banking.txt"],
  "chunks_retrieved": 3,
  "confidence": 0.92,
  "processing_time": 2.345,
  "timestamp": "2026-08-05T10:30:45.123456"
}
```

### **UI Display Example**
```
Question: What is the interest rate for savings accounts?

Answer:
The interest rate for savings accounts is 2.5% APY for balances 
$10,001-$50,000. It increases to 2.75% APY for balances over $50,001...

Confidence: 92%  |  Time: 2.35s  |  Chunks: 3

Sources:
📄 banking.txt
```

---

## **NEXT STEPS AFTER EXECUTION**

1. **Explore the Code**
   - Read README files in each part
   - Review test files for usage patterns
   - Check docstrings in main classes

2. **Customize for Your Use Case**
   - Add your own banking documents
   - Adjust RAG parameters (chunk_size, top_k)
   - Configure API keys for production

3. **Deploy to Production**
   - Use Docker for containerization
   - Set up with Kubernetes for scaling
   - Configure SSL/TLS for security
   - Use environment variables for secrets

4. **Monitor and Optimize**
   - Track query metrics
   - Analyze user feedback
   - Improve document indexing
   - Fine-tune retrieval parameters

---

## **SUPPORT RESOURCES**

- **QUICKSTART.md** - Quick reference guide
- **COMPLETE_PROJECT_SUMMARY.md** - Full system documentation
- **README.md** - Main project guide
- **PART_*_SUMMARY.md** - Individual component docs
- **Test files** - Usage examples
- **Code docstrings** - Function documentation

---

**You're all set! Follow these steps and you'll have a fully functional Banking RAG Assistant running locally. 🚀**
