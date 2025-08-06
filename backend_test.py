import requests
import sys
import json
from datetime import datetime, timezone
import uuid

class AIVoiceAssistantTester:
    def __init__(self, base_url="https://2867aa8a-d790-4560-bca8-0aa95bc7839e.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = "unity_dev_001"  # Test user ID as specified

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )

    def test_create_conversation(self):
        """Test creating a conversation"""
        conversation_data = {
            "id": f"conv_{uuid.uuid4()}",
            "user_id": self.user_id,
            "message": "Hello, can you help me with Unity development?",
            "response": "Of course! I'm here to help with your Unity projects.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {"topic": "unity_help"}
        }
        
        success, response = self.run_test(
            "Create Conversation",
            "POST",
            "api/conversations",
            200,
            data=conversation_data
        )
        return success, conversation_data["id"] if success else None

    def test_get_conversations(self):
        """Test getting conversations for user"""
        return self.run_test(
            "Get Conversations",
            "GET",
            f"api/conversations/{self.user_id}",
            200
        )

    def test_create_project(self):
        """Test creating a Unity project"""
        project_data = {
            "id": f"project_{uuid.uuid4()}",
            "user_id": self.user_id,
            "name": "Test Unity Game",
            "description": "A test game project for the AI assistant",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_modified": datetime.now(timezone.utc).isoformat(),
            "scripts": [],
            "status": "active"
        }
        
        success, response = self.run_test(
            "Create Project",
            "POST",
            "api/projects",
            200,
            data=project_data
        )
        return success, project_data["id"] if success else None

    def test_get_projects(self):
        """Test getting projects for user"""
        return self.run_test(
            "Get Projects",
            "GET",
            f"api/projects/{self.user_id}",
            200
        )

    def test_update_project(self, project_id):
        """Test updating a project"""
        if not project_id:
            print("⚠️  Skipping project update test - no project ID available")
            return False, {}
            
        update_data = {
            "description": "Updated description for the test project",
            "status": "in_progress"
        }
        
        return self.run_test(
            "Update Project",
            "PUT",
            f"api/projects/{project_id}",
            200,
            data=update_data
        )

    def test_create_task(self):
        """Test creating a task"""
        task_data = {
            "id": f"task_{uuid.uuid4()}",
            "user_id": self.user_id,
            "title": "Implement player movement",
            "description": "Create a script for basic player movement in Unity",
            "priority": "high",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "due_date": None,
            "project_id": None
        }
        
        success, response = self.run_test(
            "Create Task",
            "POST",
            "api/tasks",
            200,
            data=task_data
        )
        return success, task_data["id"] if success else None

    def test_get_tasks(self):
        """Test getting tasks for user"""
        return self.run_test(
            "Get Tasks",
            "GET",
            f"api/tasks/{self.user_id}",
            200
        )

    def test_update_task(self, task_id):
        """Test updating a task"""
        if not task_id:
            print("⚠️  Skipping task update test - no task ID available")
            return False, {}
            
        update_data = {
            "status": "completed",
            "priority": "medium"
        }
        
        return self.run_test(
            "Update Task",
            "PUT",
            f"api/tasks/{task_id}",
            200,
            data=update_data
        )

    def test_create_memory(self):
        """Test creating user memory"""
        memory_data = {
            "id": f"memory_{uuid.uuid4()}",
            "user_id": self.user_id,
            "key": "preferred_coding_style",
            "value": "Clean code with detailed comments",
            "category": "coding_preferences",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return self.run_test(
            "Create Memory",
            "POST",
            "api/memory",
            200,
            data=memory_data
        )

    def test_get_memory(self):
        """Test getting user memory"""
        return self.run_test(
            "Get Memory",
            "GET",
            f"api/memory/{self.user_id}",
            200
        )

    def test_generate_script(self):
        """Test Unity script generation"""
        script_data = {
            "user_id": self.user_id,
            "script_type": "PlayerController",
            "description": "A basic player controller for 2D platformer game"
        }
        
        return self.run_test(
            "Generate Unity Script",
            "POST",
            "api/generate-script",
            200,
            data=script_data
        )

    def test_realtime_session(self):
        """Test OpenAI realtime session creation"""
        return self.run_test(
            "OpenAI Realtime Session",
            "POST",
            "api/v1/realtime/session",
            200,
            data={}
        )

def main():
    print("🚀 Starting AI Voice Assistant Backend Tests")
    print("=" * 60)
    
    tester = AIVoiceAssistantTester()
    
    # Test health check first
    health_success, _ = tester.test_health_check()
    if not health_success:
        print("❌ Health check failed - backend may not be running")
        return 1

    # Test conversation endpoints
    conv_success, conv_id = tester.test_create_conversation()
    tester.test_get_conversations()

    # Test project endpoints
    proj_success, proj_id = tester.test_create_project()
    tester.test_get_projects()
    if proj_success:
        tester.test_update_project(proj_id)

    # Test task endpoints
    task_success, task_id = tester.test_create_task()
    tester.test_get_tasks()
    if task_success:
        tester.test_update_task(task_id)

    # Test memory endpoints
    tester.test_create_memory()
    tester.test_get_memory()

    # Test Unity script generation
    tester.test_generate_script()

    # Test OpenAI realtime session (may fail if API key issues)
    tester.test_realtime_session()

    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())