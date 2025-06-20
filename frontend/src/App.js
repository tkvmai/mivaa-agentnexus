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
} from '@mui/material';
import {
  Send as SendIcon,
  Refresh as RefreshIcon,
  ExpandLess,
  ExpandMore,
  HelpOutline as HelpIcon,
} from '@mui/icons-material';
import axios from 'axios';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

const API_BASE_URL = '/api';

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
];

const lasTools = [
  { tool: 'las_parser', purpose: 'Extract metadata & curves', example: 'Parse all matching well_*.las' },
  { tool: 'las_analysis', purpose: 'Statistical curve analysis', example: 'Analyze GR and RHOB curves in well_1.las' },
  { tool: 'las_qc', purpose: 'Data validation', example: 'Check quality of problematic_well.las' },
  { tool: 'formation_evaluation', purpose: 'Petrophysical analysis', example: 'Evaluate formation in reservoir.las' },
  { tool: 'well_correlation', purpose: 'Multi-well correlation', example: 'Correlate formations across field_*.las' },
  { tool: 'calculate_shale_volume', purpose: 'Gamma ray shale volume', example: 'Calculate shale volume using Larionov' },
];

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [groupedFiles, setGroupedFiles] = useState({});
  const [openCategories, setOpenCategories] = useState({ 'Well Logs': true, 'Seismic': true, 'Other': true });
  const [helpOpen, setHelpOpen] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);
  const [filesError, setFilesError] = useState(null);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    setFilesLoading(true);
    setFilesError(null);
    try {
      const res = await axios.get(`${API_BASE_URL}/files`);
      const files = res.data.content || [];
      
      const groups = {
        'Well Logs': [],
        'Seismic': [],
        'Other': [],
      };

      files.forEach(fileObj => {
        let filename = '';
        if (typeof fileObj === 'object' && fileObj !== null) {
          filename = fileObj.file || fileObj.name || '';
        } else if (typeof fileObj === 'string') {
          filename = fileObj;
        }

        if (filename.toLowerCase().endsWith('.las')) {
          groups['Well Logs'].push(filename);
        } else if (filename.toLowerCase().endsWith('.sgy') || filename.toLowerCase().endsWith('.segy')) {
          groups['Seismic'].push(filename);
        } else if (filename) {
          groups['Other'].push(filename);
        }
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
    setResponse('');
    try {
      const response = await axios.post(`${API_BASE_URL}/query`, { query });
      setResponse(response.data.response);
    } catch (error) {
      setResponse(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  const handleCategoryClick = (category) => {
    setOpenCategories(prev => ({ ...prev, [category]: !prev[category] }));
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <CssBaseline />
      <AppBar position="static" sx={{ backgroundColor: '#005A9C' }}>
        <Toolbar>
          <img src="/logo.png" alt="Company Logo" style={{ height: '40px', marginRight: '16px', backgroundColor: 'white', padding: '4px', borderRadius: '4px' }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            i2G AGENTIC AI
          </Typography>
          <IconButton color="inherit" onClick={fetchFiles}>
            <RefreshIcon />
          </IconButton>
          <IconButton color="inherit" onClick={() => setHelpOpen(true)}>
            <HelpIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        <Grid container sx={{ height: '100%' }}>
          {/* Left Panel */}
          <Grid item xs={12} md={4} sx={{
            display: 'flex',
            flexDirection: 'column',
            p: 2,
            borderRight: { md: '1px solid #ddd' },
            height: '100%',
            overflowY: 'auto'
          }}>
            <Paper sx={{ p: 2, flexGrow: 1, overflowY: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Available Files
              </Typography>
               {filesLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                  <CircularProgress />
                </Box>
              ) : filesError ? (
                <Typography color="error">{filesError}</Typography>
              ) : (Object.values(groupedFiles).every(arr => arr.length === 0)) ? (
                <Typography variant="body2">No available files found.</Typography>
              ) : (
                <List component="nav" dense>
                  {Object.entries(groupedFiles).map(([category, files]) => (
                    (files && files.length > 0) && (
                      <React.Fragment key={category}>
                        <ListItem button onClick={() => handleCategoryClick(category)}>
                          <ListItemText primary={`${category} (${files.length})`} />
                          {openCategories[category] ? <ExpandLess /> : <ExpandMore />}
                        </ListItem>
                        <Collapse in={openCategories[category]} timeout="auto" unmountOnExit>
                          <List component="div" disablePadding dense>
                            {files.map((file, index) => (
                              <ListItem key={index} sx={{ pl: 4 }}>
                                <ListItemText primary={file} primaryTypographyProps={{ style: { whiteSpace: "normal" } }}/>
                              </ListItem>
                            ))}
                          </List>
                        </Collapse>
                      </React.Fragment>
                    )
                  ))}
                </List>
              )}
            </Paper>
          </Grid>

          {/* Right Panel */}
          <Grid item xs={12} md={8} sx={{ display: 'flex', flexDirection: 'column', height: '100%', p: 2 }}>
            <Paper component="form" onSubmit={handleSubmit} sx={{ p: 2, flexShrink: 0, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Query Agent
              </Typography>
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
              >
                Submit Query
              </Button>
            </Paper>

            <Paper sx={{ p: 2, flexGrow: 1, overflowY: 'auto', bgcolor: '#282c34' }}>
              <Typography variant="h6" gutterBottom sx={{ color: 'white' }}>
                Response
              </Typography>
              {loading && !response && (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <CircularProgress />
                </Box>
              )}
              {response && (
                 <Box sx={{
                      bgcolor: '#282c34',
                      borderRadius: 1,
                      p: 1
                    }}>
                  <SyntaxHighlighter language="text" style={atomOneDark} customStyle={{ margin: 0, padding: '1rem', backgroundColor: '#282c34' }}>
                    {String(response)}
                  </SyntaxHighlighter>
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>

      <Dialog open={helpOpen} onClose={() => setHelpOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Available Tools and Usage Examples</DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom>SEG-Y Seismic Analysis Tools ({segyTools.length})</Typography>
          <TableContainer component={Paper} sx={{mb: 4}}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{fontWeight: 'bold'}}>Tool</TableCell>
                  <TableCell sx={{fontWeight: 'bold'}}>Purpose</TableCell>
                  <TableCell sx={{fontWeight: 'bold'}}>Example Usage</TableCell>
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
                  <TableCell sx={{fontWeight: 'bold'}}>Tool</TableCell>
                  <TableCell sx={{fontWeight: 'bold'}}>Purpose</TableCell>
                  <TableCell sx={{fontWeight: 'bold'}}>Example Usage</TableCell>
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