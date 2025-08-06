import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, User, Bot, Code, Calendar, Settings, Play, Square, Volume2, VolumeX } from 'lucide-react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { ScrollArea } from './components/ui/scroll-area';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import './App.css';

// RealtimeAudioChat class for voice communication
class RealtimeAudioChat {
    constructor() {
        this.peerConnection = null;
        this.dataChannel = null;
        this.audioElement = null;
        this.isConnected = false;
    }

    async init() {
        try {
            const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
            
            // Get session from backend
            const tokenResponse = await fetch(`${backendUrl}/api/v1/realtime/session`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            });
            const data = await tokenResponse.json();
            if (!data.client_secret?.value) {
                throw new Error("Failed to get session token");
            }

            // Create and set up WebRTC peer connection
            this.peerConnection = new RTCPeerConnection();
            this.setupAudioElement();
            await this.setupLocalAudio();
            this.setupDataChannel();

            // Create and send offer
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);

            // Send offer to backend and get answer
            const response = await fetch(`${backendUrl}/api/v1/realtime/negotiate`, {
                method: "POST",
                body: offer.sdp,
                headers: {
                    "Content-Type": "application/sdp"
                }
            });

            const { sdp: answerSdp } = await response.json();
            const answer = {
                type: "answer",
                sdp: answerSdp
            };

            await this.peerConnection.setRemoteDescription(answer);
            this.isConnected = true;
            console.log("WebRTC connection established");
        } catch (error) {
            console.error("Failed to initialize audio chat:", error);
            throw error;
        }
    }

    setupAudioElement() {
        this.audioElement = document.createElement("audio");
        this.audioElement.autoplay = true;
        document.body.appendChild(this.audioElement);

        this.peerConnection.ontrack = (event) => {
            this.audioElement.srcObject = event.streams[0];
        };
    }

    async setupLocalAudio() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => {
            this.peerConnection.addTrack(track, stream);
        });
    }

    setupDataChannel() {
        this.dataChannel = this.peerConnection.createDataChannel("oai-events");
        this.dataChannel.onmessage = (event) => {
            console.log("Received event:", event.data);
        };
    }

    disconnect() {
        if (this.peerConnection) {
            this.peerConnection.close();
            this.isConnected = false;
        }
        if (this.audioElement) {
            document.body.removeChild(this.audioElement);
        }
    }
}

function App() {
    const [isListening, setIsListening] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [conversations, setConversations] = useState([]);
    const [projects, setProjects] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [activeTab, setActiveTab] = useState('chat');
    const [userId] = useState('unity_dev_001'); // For demo purposes
    const [newTask, setNewTask] = useState('');
    const [projectName, setProjectName] = useState('');
    const [projectDescription, setProjectDescription] = useState('');
    
    const audioChat = useRef(null);
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

    useEffect(() => {
        loadUserData();
    }, []);

    const loadUserData = async () => {
        try {
            // Load conversations
            const convResponse = await fetch(`${backendUrl}/api/conversations/${userId}`);
            if (convResponse.ok) {
                const convData = await convResponse.json();
                setConversations(convData);
            }

            // Load projects
            const projResponse = await fetch(`${backendUrl}/api/projects/${userId}`);
            if (projResponse.ok) {
                const projData = await projResponse.json();
                setProjects(projData);
            }

            // Load tasks
            const taskResponse = await fetch(`${backendUrl}/api/tasks/${userId}`);
            if (taskResponse.ok) {
                const taskData = await taskResponse.json();
                setTasks(taskData);
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    };

    const toggleVoiceConnection = async () => {
        if (!isConnected) {
            try {
                audioChat.current = new RealtimeAudioChat();
                await audioChat.current.init();
                setIsConnected(true);
                setIsListening(true);
            } catch (error) {
                console.error('Failed to connect voice chat:', error);
                alert('Failed to connect voice chat. Please check your microphone permissions.');
            }
        } else {
            if (audioChat.current) {
                audioChat.current.disconnect();
                audioChat.current = null;
            }
            setIsConnected(false);
            setIsListening(false);
        }
    };

    const toggleMute = () => {
        setIsMuted(!isMuted);
        // Implement actual mute functionality here
    };

    const createTask = async () => {
        if (!newTask.trim()) return;
        
        try {
            const task = {
                id: `task_${Date.now()}`,
                user_id: userId,
                title: newTask,
                description: '',
                created_at: new Date().toISOString(),
                status: 'pending',
                priority: 'medium'
            };

            const response = await fetch(`${backendUrl}/api/tasks`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(task)
            });

            if (response.ok) {
                setTasks([task, ...tasks]);
                setNewTask('');
            }
        } catch (error) {
            console.error('Error creating task:', error);
        }
    };

    const createProject = async () => {
        if (!projectName.trim()) return;
        
        try {
            const project = {
                id: `project_${Date.now()}`,
                user_id: userId,
                name: projectName,
                description: projectDescription,
                created_at: new Date().toISOString(),
                last_modified: new Date().toISOString(),
                status: 'active'
            };

            const response = await fetch(`${backendUrl}/api/projects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(project)
            });

            if (response.ok) {
                setProjects([project, ...projects]);
                setProjectName('');
                setProjectDescription('');
            }
        } catch (error) {
            console.error('Error creating project:', error);
        }
    };

    const generateScript = async (scriptType, description) => {
        try {
            const response = await fetch(`${backendUrl}/api/generate-script`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId,
                    script_type: scriptType,
                    description: description
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Generated script:', data.script);
                // You can display this in a modal or copy to clipboard
            }
        } catch (error) {
            console.error('Error generating script:', error);
        }
    };

    return (
        <div className="app-container">
            {/* Header */}
            <header className="app-header">
                <div className="header-content">
                    <div className="logo-section">
                        <Bot className="logo-icon" />
                        <h1 className="app-title">Unity AI Assistant</h1>
                    </div>
                    <div className="voice-controls">
                        <Button
                            onClick={toggleMute}
                            variant={isMuted ? "destructive" : "outline"}
                            size="sm"
                            className="mute-button"
                        >
                            {isMuted ? <VolumeX /> : <Volume2 />}
                        </Button>
                        <Button
                            onClick={toggleVoiceConnection}
                            variant={isConnected ? "destructive" : "default"}
                            size="lg"
                            className="voice-button"
                        >
                            {isConnected ? <Square className="mr-2" /> : <Play className="mr-2" />}
                            {isConnected ? 'Disconnect' : 'Connect Voice'}
                        </Button>
                        <div className="connection-status">
                            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></div>
                            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="main-content">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="main-tabs">
                    <TabsList className="tabs-list">
                        <TabsTrigger value="chat">
                            <Bot className="mr-2 h-4 w-4" />
                            Chat
                        </TabsTrigger>
                        <TabsTrigger value="projects">
                            <Code className="mr-2 h-4 w-4" />
                            Projects
                        </TabsTrigger>
                        <TabsTrigger value="tasks">
                            <Calendar className="mr-2 h-4 w-4" />
                            Tasks
                        </TabsTrigger>
                        <TabsTrigger value="settings">
                            <Settings className="mr-2 h-4 w-4" />
                            Settings
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="chat" className="tab-content">
                        <Card className="chat-card">
                            <CardHeader>
                                <CardTitle className="flex items-center">
                                    <Bot className="mr-2 h-5 w-5" />
                                    Voice Chat with AI
                                    <Badge variant={isListening ? "default" : "secondary"} className="ml-2">
                                        {isListening ? "Listening" : "Offline"}
                                    </Badge>
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="chat-interface">
                                    <ScrollArea className="chat-history">
                                        {conversations.length === 0 ? (
                                            <div className="empty-chat">
                                                <Bot className="empty-icon" />
                                                <p>Start talking to your AI assistant!</p>
                                                <p className="text-sm text-muted-foreground">
                                                    Click "Connect Voice" to begin a conversation
                                                </p>
                                            </div>
                                        ) : (
                                            conversations.map((conv, index) => (
                                                <div key={index} className="conversation-item">
                                                    <div className="message user-message">
                                                        <User className="message-icon" />
                                                        <span>{conv.message}</span>
                                                    </div>
                                                    <div className="message ai-message">
                                                        <Bot className="message-icon" />
                                                        <span>{conv.response}</span>
                                                    </div>
                                                </div>
                                            ))
                                        )}
                                    </ScrollArea>
                                    <div className="voice-indicator">
                                        <div className={`voice-wave ${isListening ? 'active' : ''}`}>
                                            <div className="wave-bar"></div>
                                            <div className="wave-bar"></div>
                                            <div className="wave-bar"></div>
                                            <div className="wave-bar"></div>
                                            <div className="wave-bar"></div>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="projects" className="tab-content">
                        <div className="projects-section">
                            <Card className="create-project-card">
                                <CardHeader>
                                    <CardTitle>Create New Unity Project</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <Input
                                        placeholder="Project Name"
                                        value={projectName}
                                        onChange={(e) => setProjectName(e.target.value)}
                                    />
                                    <Textarea
                                        placeholder="Project Description"
                                        value={projectDescription}
                                        onChange={(e) => setProjectDescription(e.target.value)}
                                    />
                                    <Button onClick={createProject} disabled={!projectName.trim()}>
                                        Create Project
                                    </Button>
                                </CardContent>
                            </Card>

                            <div className="projects-grid">
                                {projects.map((project) => (
                                    <Card key={project.id} className="project-card">
                                        <CardHeader>
                                            <CardTitle className="flex items-center justify-between">
                                                <span>{project.name}</span>
                                                <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                                                    {project.status}
                                                </Badge>
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <p className="text-sm text-muted-foreground">{project.description}</p>
                                            <div className="project-actions mt-4">
                                                <Button size="sm" variant="outline">
                                                    Open Scripts
                                                </Button>
                                                <Button size="sm" variant="outline">
                                                    Generate Code
                                                </Button>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="tasks" className="tab-content">
                        <div className="tasks-section">
                            <Card className="create-task-card">
                                <CardHeader>
                                    <CardTitle>Add New Task</CardTitle>
                                </CardHeader>
                                <CardContent className="flex space-x-2">
                                    <Input
                                        placeholder="Enter a new task..."
                                        value={newTask}
                                        onChange={(e) => setNewTask(e.target.value)}
                                        onKeyPress={(e) => e.key === 'Enter' && createTask()}
                                    />
                                    <Button onClick={createTask} disabled={!newTask.trim()}>
                                        Add Task
                                    </Button>
                                </CardContent>
                            </Card>

                            <div className="tasks-list">
                                {tasks.map((task) => (
                                    <Card key={task.id} className="task-card">
                                        <CardContent className="flex items-center justify-between">
                                            <div className="task-info">
                                                <h3 className="font-medium">{task.title}</h3>
                                                <div className="flex items-center space-x-2 mt-1">
                                                    <Badge variant="outline">{task.priority}</Badge>
                                                    <Badge variant={task.status === 'completed' ? 'default' : 'secondary'}>
                                                        {task.status}
                                                    </Badge>
                                                </div>
                                            </div>
                                            <Button size="sm" variant="outline">
                                                Complete
                                            </Button>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="settings" className="tab-content">
                        <Card>
                            <CardHeader>
                                <CardTitle>Assistant Settings</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="setting-group">
                                    <h3 className="font-medium">Voice Settings</h3>
                                    <div className="space-y-2">
                                        <Button variant="outline" size="sm">
                                            Test Microphone
                                        </Button>
                                        <Button variant="outline" size="sm">
                                            Adjust Voice Recognition
                                        </Button>
                                    </div>
                                </div>
                                <div className="setting-group">
                                    <h3 className="font-medium">Unity Integration</h3>
                                    <div className="space-y-2">
                                        <Button variant="outline" size="sm">
                                            Set Unity Path
                                        </Button>
                                        <Button variant="outline" size="sm">
                                            Configure Code Templates
                                        </Button>
                                    </div>
                                </div>
                                <div className="setting-group">
                                    <h3 className="font-medium">Memory & Privacy</h3>
                                    <div className="space-y-2">
                                        <Button variant="outline" size="sm">
                                            Clear Conversation History
                                        </Button>
                                        <Button variant="outline" size="sm">
                                            Export Data
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </main>
        </div>
    );
}

export default App;