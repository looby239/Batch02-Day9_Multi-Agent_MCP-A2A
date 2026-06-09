import { useState, useRef, useEffect, useCallback } from 'react';
import { ReactFlow, Background, Controls, MarkerType, useNodesState, useEdgesState } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Send, User, Server, Scale, Calculator, ShieldCheck, BrainCircuit } from 'lucide-react';
import './index.css';

// Custom Node Component
const AgentNode = ({ data }) => {
  return (
    <div className={`custom-node ${data.active ? 'active' : ''}`} style={{ borderColor: data.color }}>
      <div className="icon" style={{ color: data.color }}>
        {data.icon}
      </div>
      <div>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{data.type}</div>
        <div>{data.label}</div>
      </div>
    </div>
  );
};

const nodeTypes = { agent: AgentNode };

// UUID generator
const uuidv4 = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

const initialNodes = [
  { id: 'user', type: 'agent', position: { x: 50, y: 250 }, data: { label: 'User', type: 'Client', icon: <User size={20}/>, color: '#3b82f6' } },
  { id: 'customer', type: 'agent', position: { x: 300, y: 250 }, data: { label: 'Customer Agent', type: 'Gateway', icon: <Server size={20}/>, color: '#8b5cf6' } },
  { id: 'registry', type: 'agent', position: { x: 550, y: 100 }, data: { label: 'Registry', type: 'Discovery', icon: <BrainCircuit size={20}/>, color: '#ec4899' } },
  { id: 'law', type: 'agent', position: { x: 550, y: 250 }, data: { label: 'Law Agent', type: 'Orchestrator', icon: <Scale size={20}/>, color: '#10b981' } },
  { id: 'tax', type: 'agent', position: { x: 800, y: 150 }, data: { label: 'Tax Agent', type: 'Specialist', icon: <Calculator size={20}/>, color: '#f59e0b' } },
  { id: 'compliance', type: 'agent', position: { x: 800, y: 350 }, data: { label: 'Compliance Agent', type: 'Specialist', icon: <ShieldCheck size={20}/>, color: '#0ea5e9' } }
];

const initialEdges = [
  { id: 'e1', source: 'user', target: 'customer', animated: false, style: { stroke: '#ffffff55' } },
  { id: 'e2', source: 'customer', target: 'registry', animated: false, style: { stroke: '#ffffff55' } },
  { id: 'e3', source: 'customer', target: 'law', animated: false, style: { stroke: '#ffffff55' } },
  { id: 'e4', source: 'law', target: 'registry', animated: false, style: { stroke: '#ffffff55' } },
  { id: 'e5', source: 'law', target: 'tax', animated: false, style: { stroke: '#ffffff55' } },
  { id: 'e6', source: 'law', target: 'compliance', animated: false, style: { stroke: '#ffffff55' } }
];

function App() {
  const [messages, setMessages] = useState([
    { id: 'welcome', role: 'agent', content: 'Welcome to the Multi-Agent Legal Assistant. Ask a question about tax or compliance to see the pipeline in action!' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const activateFlow = async () => {
    // Sequence of animations
    const delay = (ms) => new Promise(res => setTimeout(res, ms));
    
    const highlightNode = (id, active) => {
      setNodes(nds => nds.map(n => n.id === id ? { ...n, data: { ...n.data, active } } : n));
    };
    const animateEdge = (id, animated, color = '#6366f1') => {
      setEdges(eds => eds.map(e => e.id === id ? { 
        ...e, 
        animated, 
        style: { stroke: color, strokeWidth: animated ? 3 : 1 },
        markerEnd: animated ? { type: MarkerType.ArrowClosed, color } : undefined
      } : e));
    };

    // User -> Customer
    highlightNode('user', true);
    animateEdge('e1', true);
    await delay(600);
    highlightNode('user', false);
    animateEdge('e1', false, '#ffffff55');
    highlightNode('customer', true);

    // Customer -> Registry
    animateEdge('e2', true, '#ec4899');
    await delay(600);
    animateEdge('e2', false, '#ffffff55');

    // Customer -> Law
    animateEdge('e3', true, '#10b981');
    await delay(600);
    highlightNode('customer', false);
    animateEdge('e3', false, '#ffffff55');
    highlightNode('law', true);

    // Law -> Tax & Compliance
    animateEdge('e5', true, '#f59e0b');
    animateEdge('e6', true, '#0ea5e9');
    await delay(600);
    highlightNode('tax', true);
    highlightNode('compliance', true);
    
    await delay(1500); // Processing time

    // Return path
    animateEdge('e5', false, '#ffffff55');
    animateEdge('e6', false, '#ffffff55');
    highlightNode('tax', false);
    highlightNode('compliance', false);
    await delay(600);

    highlightNode('law', false);
    highlightNode('customer', true);
    await delay(600);
    highlightNode('customer', false);
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { id: uuidv4(), role: 'user', content: userMsg }]);
    setLoading(true);

    activateFlow(); // Start animation in background

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: "2.0",
          method: "agent/sendMessage",
          id: uuidv4(),
          params: { message: { role: 'user', parts: [{ text: userMsg }], message_id: uuidv4() } }
        })
      });

      const data = await response.json();
      let replyText = "Failed to parse response.";
      
      if (data.result && data.result.artifacts && data.result.artifacts.length > 0) {
          const artifact = data.result.artifacts[0];
          if (artifact.parts && artifact.parts.length > 0) {
              replyText = artifact.parts[0].text;
          }
      } else if (data.result && data.result.parts && data.result.parts.length > 0) {
          replyText = data.result.parts[0].text;
      } else if (data.error) {
          replyText = `Error: ${data.error.message || JSON.stringify(data.error)}`;
      }

      setMessages(prev => [...prev, { id: uuidv4(), role: 'agent', content: replyText }]);
    } catch (err) {
      setMessages(prev => [...prev, { id: uuidv4(), role: 'agent', content: `Connection error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      {/* Chat Panel */}
      <div className="chat-panel">
        <div className="chat-header">
          <h1>Customer Agent (A2A)</h1>
        </div>
        
        <div className="chat-messages">
          {messages.map(msg => (
            <div key={msg.id} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
          {loading && (
            <div className="message agent" style={{ opacity: 0.7, fontStyle: 'italic' }}>
              Thinking... (Watch the graph)
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input" onSubmit={handleSend}>
          <div className="input-wrapper">
            <input 
              type="text" 
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about corporate tax laws..."
              disabled={loading}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              <Send size={18} />
            </button>
          </div>
        </form>
      </div>

      {/* ReactFlow Visualizer */}
      <div className="flow-panel">
        <ReactFlow 
          nodes={nodes} 
          edges={edges} 
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          colorMode="dark"
        >
          <Background color="#ffffff22" gap={16} />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}

export default App;
