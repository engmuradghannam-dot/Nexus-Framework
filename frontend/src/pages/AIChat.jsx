import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Typography, Paper, TextField, Button, List, ListItem,
  Avatar, Divider, CircularProgress, IconButton, Drawer
} from '@mui/material';
import { Send, SmartToy, Person, Add, History } from '@mui/icons-material';
import { getAIModels, createConversation, sendMessage, api } from '../api';

export default function AIChat() {
  const [conversations, setConversations] = useState([]);
  const [currentConv, setCurrentConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadModels();
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadModels = async () => {
    try {
      const res = await getAIModels();
      setModels(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadConversations = async () => {
    try {
      const res = await api.get('/ai/conversations/');
      setConversations(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewChat = async () => {
    if (models.length === 0) return;
    try {
      const res = await createConversation({
        model_id: models[0].id,
        title: 'New Conversation',
        content: 'Hello!'
      });
      setCurrentConv(res.data);
      setMessages([
        { role: 'user', content: 'Hello!' },
        res.data.assistant_message
      ]);
      loadConversations();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !currentConv) return;
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await sendMessage(currentConv.conversation?.id || currentConv.id, input);
      setMessages(prev => [...prev, res.data.assistant_message]);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 140px)' }}>
      <Drawer variant="permanent" sx={{ width: 260, flexShrink: 0, '& .MuiDrawer-paper': { width: 260 } }}>
        <Box sx={{ p: 2 }}>
          <Button
            fullWidth variant="contained" startIcon={<Add />}
            onClick={handleNewChat} sx={{ mb: 2 }}
          >
            New Chat
          </Button>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            <History fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />
            History
          </Typography>
          <List dense>
            {conversations.map(conv => (
              <ListItem
                key={conv.id}
                button
                selected={currentConv?.id === conv.id}
                onClick={() => setCurrentConv(conv)}
              >
                <Typography noWrap variant="body2">{conv.title || 'Untitled'}</Typography>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', ml: '260px' }}>
        <Paper sx={{ flexGrow: 1, mb: 2, p: 2, overflow: 'auto' }}>
          {!currentConv ? (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <Typography color="text.secondary">Start a new conversation</Typography>
            </Box>
          ) : (
            <List>
              {messages.map((msg, idx) => (
                <ListItem key={idx} sx={{ alignItems: 'flex-start', gap: 2 }}>
                  <Avatar sx={{ bgcolor: msg.role === 'assistant' ? 'primary.main' : 'secondary.main' }}>
                    {msg.role === 'assistant' ? <SmartToy /> : <Person />}
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle2" fontWeight="bold">
                      {msg.role === 'assistant' ? 'AI Assistant' : 'You'}
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </Typography>
                  </Box>
                </ListItem>
              ))}
              {loading && (
                <ListItem>
                  <CircularProgress size={24} />
                </ListItem>
              )}
              <div ref={messagesEndRef} />
            </List>
          )}
        </Paper>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth variant="outlined" placeholder="Type your message..."
            value={input} onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            disabled={!currentConv || loading}
          />
          <Button
            variant="contained" onClick={handleSend}
            disabled={!currentConv || loading || !input.trim()}
          >
            <Send />
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
