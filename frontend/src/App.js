import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
  AppBar,
  Toolbar,
  IconButton,
} from '@mui/material';
import { Send as SendIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import axios from 'axios';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const API_BASE_URL = 'http://ddns.i2g.cloud:8000/api';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetchFiles();
    fetchStatus();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/files`);
      setFiles(response.data.content || []);
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status`);
      setStatus(response.data);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/query`, { query });
      setResponse(response.data.response);
    } catch (error) {
      setResponse(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Subsurface Data Management Platform
          </Typography>
          <IconButton color="inherit" onClick={fetchStatus}>
            <RefreshIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
          {/* Left Panel - Files and Status */}
          <Box>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Available Files
              </Typography>
              <List>
                {files.map((fileObj, index) => {
                  let displayName = fileObj;
                  if (typeof fileObj === 'object' && fileObj !== null) {
                    displayName = fileObj.file || fileObj.name || JSON.stringify(fileObj);
                  }
                  return (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemText primary={displayName} />
                      </ListItem>
                      {index < files.length - 1 && <Divider />}
                    </React.Fragment>
                  );
                })}
              </List>
            </Paper>

            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              {status && (
                <Box>
                  <Typography variant="body2">
                    Uptime: {status.uptime_hours?.toFixed(2)} hours
                  </Typography>
                  <Typography variant="body2">
                    Total Queries: {status.total_queries}
                  </Typography>
                  <Typography variant="body2">
                    System Type: {status.system_type}
                  </Typography>
                </Box>
              )}
            </Paper>
          </Box>

          {/* Right Panel - Query Interface */}
          <Box>
            <Paper sx={{ p: 2, height: '100%' }}>
              <form onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  variant="outlined"
                  label="Enter your query"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  sx={{ mb: 2 }}
                />
                <Button
                  variant="contained"
                  endIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                  type="submit"
                  disabled={loading}
                >
                  Submit Query
                </Button>
              </form>

              {response && (
                <Box sx={{ mt: 4 }}>
                  <Typography variant="h6" gutterBottom>
                    Response
                  </Typography>
                  <Paper
                    sx={{
                      p: 2,
                      bgcolor: '#f5f5f5',
                      maxHeight: '400px',
                      overflow: 'auto',
                    }}
                  >
                    <SyntaxHighlighter language="text" style={docco}>
                      {response}
                    </SyntaxHighlighter>
                  </Paper>
                </Box>
              )}
            </Paper>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

export default App; 