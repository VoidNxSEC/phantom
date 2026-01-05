# Test CORTEX Chat API

# Test 1: Simple chat without context
echo "=== Test 1: Chat without knowledge base ==="
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, who are you?",
    "conversation_id": "test_001",
    "history": [],
    "context_size": 5
  }' | jq .

echo -e "\n\n=== Test 2: Chat asking about Python (requires processed docs) ==="
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I handle errors in Python?",
    "conversation_id": "test_002",
    "history": [],
    "context_size": 5
  }' | jq .

echo -e "\n\n=== Test 3: Follow-up question (with history) ==="
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can you show me an example?",
    "conversation_id": "test_002",
    "history": [
      {"role": "user", "content": "How do I handle errors in Python?"},
      {"role": "assistant", "content": "Use try-except blocks..."}
    ],
    "context_size": 5
  }' | jq .
