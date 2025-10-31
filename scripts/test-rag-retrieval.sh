#!/bin/bash
# Test RAG retrieval to debug why cisco-ios-command-reference.md isn't being retrieved

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "Testing RAG Retrieval"
echo "========================================="

# Load environment variables
echo "Loading environment variables..."
set -a
source "$PROJECT_ROOT/.env"
set +a

# Export Python path
export PYTHONPATH="$PROJECT_ROOT"

# Run retriever test
echo "Running retrieval tests..."
python3 << 'EOF'
import sys
sys.path.insert(0, "/Users/rcampos/prog/AI/agentic-ai-unleashed")

from orchestrator.rag_retriever import LabDocumentRetriever

print("\n" + "=" * 80)
print("RAG Retrieval Test - Debugging cisco-ios-command-reference.md")
print("=" * 80)

retriever = LabDocumentRetriever()

# Test query 1: What the user tried
print("\n\n[TEST 1] Query: 'Cisco IOS ip address command syntax'")
print("-" * 80)
results = retriever.retrieve("Cisco IOS ip address command syntax", k=5)

for i, result in enumerate(results, 1):
    print(f"\nResult {i} (score: {result['score']:.4f}):")
    print(f"  Lab ID: {result['metadata']['lab_id']}")
    print(f"  Title: {result['metadata']['title']}")
    print(f"  Source: {result['metadata']['filename']}")
    print(f"  Content preview (first 150 chars): {result['content'][:150]}...")

# Test query 2: Direct command reference
print("\n\n[TEST 2] Query: 'ip address subnet mask configuration'")
print("-" * 80)
results = retriever.retrieve("ip address subnet mask configuration", k=5)

for i, result in enumerate(results, 1):
    print(f"\nResult {i} (score: {result['score']:.4f}):")
    print(f"  Lab ID: {result['metadata']['lab_id']}")
    print(f"  Title: {result['metadata']['title']}")
    print(f"  Content preview (first 150 chars): {result['content'][:150]}...")

# Test query 3: CIDR notation error
print("\n\n[TEST 3] Query: 'CIDR notation /24 subnet mask format'")
print("-" * 80)
results = retriever.retrieve("CIDR notation /24 subnet mask format", k=5)

for i, result in enumerate(results, 1):
    print(f"\nResult {i} (score: {result['score']:.4f}):")
    print(f"  Lab ID: {result['metadata']['lab_id']}")
    print(f"  Title: {result['metadata']['title']}")
    print(f"  Content preview (first 150 chars): {result['content'][:150]}...")

# Show all labs in index
print("\n\n[ALL LABS IN INDEX]")
print("-" * 80)
labs = retriever.get_lab_list()
for lab in labs:
    print(f"  - {lab['lab_id']}: {lab['title']}")

# Check how many chunks are from cisco-ios-command-reference
print("\n\n[CISCO IOS COMMAND REFERENCE CHUNKS]")
print("-" * 80)
cisco_chunks = [m for m in retriever.metadata if m['metadata']['lab_id'] == 'cisco-ios-command-reference']
print(f"Total chunks from cisco-ios-command-reference.md: {len(cisco_chunks)}")

if cisco_chunks:
    print("\nFirst 3 chunks from cisco-ios-command-reference:")
    for i, chunk in enumerate(cisco_chunks[:3], 1):
        print(f"\nChunk {i}:")
        print(f"  Content (first 200 chars): {chunk['content'][:200]}...")

EOF

echo ""
echo "========================================="
echo "Test complete!"
echo "========================================="
