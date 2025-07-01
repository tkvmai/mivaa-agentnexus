import React, { useState, useEffect, useCallback } from 'react';
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
  AppBar,
  Toolbar,
  IconButton,
  Grid,
  CssBaseline,
  ListSubheader,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Radio,
  ListItemButton,
  Drawer,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Send as SendIcon,
  Refresh as RefreshIcon,
  ExpandLess,
  ExpandMore,
  HelpOutline as HelpIcon,
  Description as DescriptionIcon,
  History as HistoryIcon,
  SmartToy as SmartToyIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import axios from 'axios';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api';

const segyTools = [
  { tool: 'segy_parser', purpose: 'Comprehensive metadata extraction', example: 'Parse survey_3d.sgy and extract geometry' },
  { tool: 'segy_classify', purpose: 'Survey type classification', example: 'Classify Model94_shots.segy - 2D or 3D?' },
  { tool: 'segy_qc', purpose: 'Quality control analysis', example: 'Check quality of seismic_data.sgy' },
  { tool: 'segy_analysis', purpose: 'Geometry and characteristics', example: 'Analyze survey geometry of marine_2d.sgy' },
  { tool: 'segy_survey_analysis', purpose: 'Multi-file survey processing', example: 'Process all matching 3D_*.sgy files' },
  { tool: 'segy_complete_metadata_harvester', purpose: 'Complete metadata extraction', example: 'Extract all header types from data.sgy' },
  { tool: 'segy_survey_polygon', purpose: 'Geographic boundary analysis', example: 'Generate spatial boundaries for survey.sgy' },
  { tool: 'segy_trace_outlines', purpose: 'Real-time trace visualization', example: 'Generate live trace outlines for monitoring' },
  { tool: 'quick_segy_summary', purpose: 'Fast file inventory', example: 'Summarize all SEG-Y files in directory' },
  { tool: 'segy_save_analysis', purpose: 'Result storage', example: 'Store analysis results with cataloging' },
  { tool: 'segy_analysis_catalog', purpose: 'Analysis inventory', example: 'Retrieve catalog of stored analyses' },
  { tool: 'segy_search_analyses', purpose: 'Search functionality', example: 'Search analyses by multiple criteria' },
  { tool: 'calculate_shale_volume', purpose: 'Gamma ray shale volume', example: 'Calculate shale volume using Larionov' },
];

const lasTools = [
  { tool: 'las_parser', purpose: 'Extract metadata & curves', example: 'Parse all matching well_*.las' },
  { tool: 'las_analysis', purpose: 'Statistical curve analysis', example: 'Analyze GR and RHOB curves in well_1.las' },
  { tool: 'las_qc', purpose: 'Data validation', example: 'Check quality of problematic_well.las' },
  { tool: 'formation_evaluation', purpose: 'Petrophysical analysis', example: 'Evaluate formation in reservoir.las' },
  { tool: 'well_correlation', purpose: 'Multi-well correlation', example: 'Correlate formations across field_*.las' },
];

function App() {
  const [query, setQuery] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [groupedFiles, setGroupedFiles] = useState({});
  const [openCategories, setOpenCategories] = useState({ 'Well Logs': false, 'Seismic': false, 'Other': false });
  const [helpOpen, setHelpOpen] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);
  const [filesError, setFilesError] = useState(null);
  const [panelWidth, setPanelWidth] = useState(400);
  const [isDragging, setIsDragging] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [openSessionGroups, setOpenSessionGroups] = useState({});

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const startNewChat = () => {
    setSelectedSessionId(null);
    setCurrentConversationId(null);
    setQuery('');
    setHistory([]);
  };

  const handleSessionClick = (sessionId) => {
    setSelectedSessionId(sessionId);
    setQuery('');
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const groupSessionsByMonth = (sessionsToGroup) => {
    return sessionsToGroup.reduce((acc, session) => {
      const date = new Date(session.timestamp);
      const monthYear = date.toLocaleString('default', { month: 'long', year: 'numeric' });
      if (!acc[monthYear]) acc[monthYear] = [];
      acc[monthYear].push(session);
      return acc;
    }, {});
  };

  const groupedSessions = groupSessionsByMonth(sessions);

  const handleSessionGroupClick = (groupName) => {
    setOpenSessionGroups(prev => ({ ...prev, [groupName]: !prev[groupName] }));
  };

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (isDragging) {
      const newWidth = Math.max(250, Math.min(e.clientX, window.innerWidth * 0.7));
      setPanelWidth(newWidth);
    }
  }, [isDragging]);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  useEffect(() => {
    fetchFiles();
    fetchSessions();
  }, []);

  useEffect(() => {
    if (selectedSessionId) {
      const session = sessions.find(s => s.id === selectedSessionId);
      if (session) {
        setCurrentConversationId(session.id);
        setHistory(session.history);
      }
    }
  }, [selectedSessionId, sessions]);

  const fetchSessions = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/sessions`);
      setSessions(res.data || []);
      // Auto-open the most recent session group
      if (res.data && res.data.length > 0) {
        const mostRecentDate = new Date(res.data[0].timestamp);
        const mostRecentGroup = mostRecentDate.toLocaleString('default', { month: 'long', year: 'numeric' });
        setOpenSessionGroups({ [mostRecentGroup]: true });
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const fetchFiles = async () => {
    setFilesLoading(true);
    setFilesError(null);
    try {
      const res = await axios.get(`${API_BASE_URL}/files`);
      const files = res.data.content || [];
      const groups = { 'Well Logs': [], 'Seismic': [], 'Other': [] };
      files.forEach(fileObj => {
        let filename = '';
        if (typeof fileObj === 'object' && fileObj !== null) {
          filename = fileObj.file || fileObj.name || '';
        } else if (typeof fileObj === 'string') {
          filename = fileObj;
        }
        if (filename.toLowerCase().endsWith('.las')) groups['Well Logs'].push(filename);
        else if (filename.toLowerCase().endsWith('.sgy') || filename.toLowerCase().endsWith('.segy')) groups['Seismic'].push(filename);
        else if (filename) groups['Other'].push(filename);
      });
      setGroupedFiles(groups);
    } catch (error) {
      console.error('Error fetching files:', error);
      setFilesError("Failed to fetch files. Please check API server connection and refresh.");
    } finally {
      setFilesLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    const newHistory = [...history, { role: 'user', content: query }];
    setHistory(newHistory);
    setQuery('');
    try {
      const payload = { query: query, conversation_id: currentConversationId };
      const result = await axios.post(`${API_BASE_URL}/query`, payload);
      
      const newConversationId = result.data.conversation_id;
      const newHistory = result.data.history;

      setCurrentConversationId(newConversationId);
      setHistory(newHistory);
      
      const existingSessionIndex = sessions.findIndex(s => s.id === newConversationId);
      if (existingSessionIndex > -1) {
        const updatedSessions = [...sessions];
        updatedSessions[existingSessionIndex].history = newHistory;
        updatedSessions[existingSessionIndex].timestamp = new Date().toISOString();
        setSessions(updatedSessions);
      } else {
        const newSession = {
          id: newConversationId,
          title: newHistory[0]?.content || 'New Session',
          timestamp: new Date().toISOString(),
          history: newHistory,
        };
        setSessions(prevSessions => [newSession, ...prevSessions]);
        setSelectedSessionId(newConversationId);
      }
    } catch (error) {
      const errorMessage = `Error: ${error.response?.data?.detail || error.message}`;
      setHistory(prev => [...prev, { role: 'assistant', content: errorMessage }]);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryClick = (category) => {
    setOpenCategories(prev => ({ ...prev, [category]: !prev[category] }));
  };

  const drawerContent = (
    <>
      {isMobile && (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', flexShrink: 0 }}>
          <IconButton onClick={handleDrawerToggle}>
            <CloseIcon />
          </IconButton>
        </Box>
      )}
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 2 }}>
        {/* Available Files Section */}
        <Paper sx={{ 
          p: 2, 
          display: 'flex', 
          flexDirection: 'column', 
          height: '45%', 
          minHeight: 0,
          overflow: 'hidden' 
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, flexShrink: 0 }}>
            <DescriptionIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Available Files</Typography>
          </Box>
          {filesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>
          ) : filesError ? (
            <Typography color="error">{filesError}</Typography>
          ) : (Object.values(groupedFiles).every(arr => arr.length === 0)) ? (
            <Typography variant="body2">No available files found.</Typography>
          ) : (
            <Box sx={{ flexGrow: 1, overflowY: 'auto', minHeight: 0 }}>
              <List component="nav" dense>
                {Object.entries(groupedFiles).map(([category, files]) => (
                  (files && files.length > 0) && (
                    <React.Fragment key={category}>
                      <ListItemButton onClick={() => handleCategoryClick(category)}>
                        {category === 'Well Logs' && <img src="/welllog_icon.png" alt="Well Log" style={{ width: 24, height: 24, marginRight: 8 }} />}
                        {category === 'Seismic' && <img src="/seismic_icon.png" alt="Seismic" style={{ width: 24, height: 24, marginRight: 8 }} />}
                        <ListItemText primary={`${category} (${files.length})`} />
                        {openCategories[category] ? <ExpandLess /> : <ExpandMore />}
                      </ListItemButton>
                      <Collapse in={openCategories[category]} timeout="auto" unmountOnExit>
                        <List component="div" disablePadding dense>
                          {files.map((file, index) => (
                            <ListItem key={index} sx={{ pl: 4 }}>
                              <ListItemText primary={file} primaryTypographyProps={{ style: { whiteSpace: "normal" } }} />
                            </ListItem>
                          ))}
                        </List>
                      </Collapse>
                    </React.Fragment>
                  )
                ))}
              </List>
            </Box>
          )}
        </Paper>

        {/* Sessions Section */}
        <Paper sx={{ 
          p: 2, 
          display: 'flex', 
          flexDirection: 'column', 
          height: '55%', 
          minHeight: 0,
          overflow: 'hidden' 
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, flexShrink: 0 }}>
            <HistoryIcon sx={{ mr: 1 }} />
            <Typography variant="h6">Sessions</Typography>
          </Box>
          <Box sx={{ flexGrow: 1, overflowY: 'auto', minHeight: 0 }}>
            <List component="nav" dense sx={{ p: 0 }}>
              {Object.entries(groupedSessions).map(([groupName, sessionItems]) => (
                <React.Fragment key={groupName}>
                  <ListItemButton onClick={() => handleSessionGroupClick(groupName)}>
                    <ListItemText primary={groupName} primaryTypographyProps={{ style: { fontWeight: 'bold' } }} />
                    {openSessionGroups[groupName] ? <ExpandLess /> : <ExpandMore />}
                  </ListItemButton>
                  <Collapse in={openSessionGroups[groupName]} timeout="auto" unmountOnExit>
                    <List component="div" disablePadding dense>
                      {sessionItems.map((session) => (
                        <ListItem
                          key={session.id}
                          onClick={() => handleSessionClick(session.id)}
                          secondaryAction={
                            <Radio
                              edge="end"
                              checked={selectedSessionId === session.id}
                              onChange={() => handleSessionClick(session.id)}
                              value={session.id}
                              name="session-radio-button"
                            />
                          }
                          disablePadding
                          sx={{
                            border: '1px solid #ddd',
                            borderRadius: '8px',
                            mb: 1,
                            cursor: 'pointer',
                            '&:hover': { backgroundColor: 'action.hover' },
                            ...(selectedSessionId === session.id && {
                              borderColor: '#005A9C',
                              borderWidth: '2px',
                              backgroundColor: 'action.selected'
                            }),
                            p: 1, pl: 2
                          }}
                        >
                          <ListItemText
                            primary={session.title}
                            secondary={`${new Date(session.timestamp).toLocaleString()}`}
                            primaryTypographyProps={{ style: { textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', paddingRight: '32px' } }}
                            secondaryTypographyProps={{ style: { textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', paddingRight: '32px' } }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Collapse>
                </React.Fragment>
              ))}
            </List>
          </Box>
        </Paper>
      </Box>
    </>
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ backgroundColor: '#005A9C', zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <img src="/logo.png" alt="Company Logo" style={{ height: '40px', marginRight: '16px', backgroundColor: 'white', padding: '4px', borderRadius: '4px' }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            i2G AGENTIC AI
          </Typography>
          <IconButton color="inherit" onClick={fetchFiles}>
            <RefreshIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Offset for AppBar */}
      <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }} />

      <Box sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', height: 'calc(100vh - 64px)', mt: { xs: 0, sm: 0 } }}>
        <Box
          component="nav"
          sx={{ width: { md: panelWidth }, flexShrink: { md: 0 }, height: '100%' }}
        >
          {/* Mobile Drawer */}
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{ keepMounted: true }}
            sx={{
              display: { xs: 'block', md: 'none' },
              '& .MuiDrawer-paper': { boxSizing: 'border-box', width: panelWidth, p: 2, display: 'flex', flexDirection: 'column', gap: 2, top: 56, height: 'calc(100% - 56px)' },
            }}
          >
            {drawerContent}
          </Drawer>

          {/* Desktop Drawer */}
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', md: 'flex' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: panelWidth,
                height: 'calc(100% - 64px)',
                overflow: 'hidden',
                p: 2,
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                borderRight: '1px solid #ddd',
                top: 64,
              },
            }}
            open
          >
            {drawerContent}
          </Drawer>
        </Box>

        {!isMobile && (
          <Box
            onMouseDown={handleMouseDown}
            sx={{
              width: '8px', cursor: 'col-resize', backgroundColor: isDragging ? '#005A9C' : 'transparent',
              borderLeft: '1px solid #ddd', borderRight: '1px solid #ddd',
              transition: 'background-color 0.2s', '&:hover': { backgroundColor: '#e0e0e0' }
            }}
          />
        )}

        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', p: 2, minWidth: 0 }}>
          <Paper component="form" onSubmit={handleSubmit} sx={{ p: 2, flexShrink: 0, mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SmartToyIcon sx={{ mr: 1 }} />
                <Typography variant="h6" component="div">
                  Query Agent
                </Typography>
              </Box>
              <Button
                variant="outlined"
                startIcon={<HelpIcon />}
                onClick={() => setHelpOpen(true)}
                size="small"
              >
                Example prompts
              </Button>
            </Box>
            <TextField
              fullWidth
              multiline
              rows={4}
              variant="outlined"
              placeholder="e.g., 'Parse survey_3d.sgy and extract geometry'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Button
              variant="contained"
              endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
              type="submit"
              disabled={loading}
              sx={{ mr: 1 }}
            >
              Submit Query
            </Button>
            <Button variant="text" onClick={startNewChat}>
              New Chat
            </Button>
          </Paper>

          <Paper sx={{ p: 2, flexGrow: 1, overflowY: 'auto', bgcolor: '#282c34' }}>
            <Typography variant="h6" gutterBottom sx={{ color: 'white' }}>
              Conversation
            </Typography>
            {[...history].map((item, index) => (
              <Box key={index} sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: item.role === 'user' ? '#90caf9' : '#a5d6a7', textTransform: 'capitalize' }}>
                  {item.role}
                </Typography>
                <Box sx={{ bgcolor: '#282c34', borderRadius: 1, p: 1 }}>
                  <SyntaxHighlighter language="text" style={atomOneDark} wrapLongLines={true} customStyle={{ margin: 0, padding: '1rem', backgroundColor: '#282c34' }}>
                    {String(item.content)}
                  </SyntaxHighlighter>
                </Box>
              </Box>
            ))}
            {loading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 2 }}>
                <CircularProgress />
              </Box>
            )}
          </Paper>
        </Box>
      </Box>

      <Dialog open={helpOpen} onClose={() => setHelpOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Available Tools and Usage Examples</DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom>SEG-Y Seismic Analysis Tools ({segyTools.length})</Typography>
          <TableContainer component={Paper} sx={{ mb: 4 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Tool</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Purpose</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Example Usage</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {segyTools.map(row => (
                  <TableRow key={row.tool}>
                    <TableCell><code>{row.tool}</code></TableCell>
                    <TableCell>{row.purpose}</TableCell>
                    <TableCell><code>{row.example}</code></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h6" gutterBottom>LAS Well Log Analysis Tools ({lasTools.length})</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold' }}>Tool</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Purpose</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Example Usage</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {lasTools.map(row => (
                  <TableRow key={row.tool}>
                    <TableCell><code>{row.tool}</code></TableCell>
                    <TableCell>{row.purpose}</TableCell>
                    <TableCell><code>{row.example}</code></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHelpOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default App; 