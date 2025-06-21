import React from 'react';
import {
  Paper, Typography, CircularProgress, List, ListItem, ListItemText, Box,
  ListItemButton, Collapse, Radio
} from '@mui/material';
import {
  ExpandLess, ExpandMore, Description as DescriptionIcon, History as HistoryIcon
} from '@mui/icons-material';

const DrawerContent = ({ 
  filesLoading, filesError, groupedFiles, handleCategoryClick, openCategories,
  groupedSessions, handleSessionGroupClick, openSessionGroups, handleSessionClick, selectedSessionId
}) => (
  <>
    <Paper sx={{ p: 2, flex: '1 1 50%', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
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
        <List component="nav" dense sx={{ overflowY: 'auto', flexGrow: 1 }}>
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
    <Paper sx={{ p: 2, flex: '1 1 50%', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <HistoryIcon sx={{ mr: 1 }} />
        <Typography variant="h6">Sessions</Typography>
      </Box>
      <List component="nav" dense sx={{ overflowY: 'auto', flexGrow: 1, p:0 }}>
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
                        '&:hover': {
                          backgroundColor: 'action.hover'
                        },
                        ...(selectedSessionId === session.id && {
                            borderColor: '#005A9C',
                            borderWidth: '2px',
                            backgroundColor: 'action.selected'
                        }),
                        p:1,
                        pl:2
                    }}
                  >
                    <ListItemText
                      primary={session.title}
                      secondary={`${new Date(session.timestamp).toLocaleString()}`}
                      primaryTypographyProps={{ 
                        style: { 
                          textOverflow: 'ellipsis', 
                          overflow: 'hidden', 
                          whiteSpace: 'nowrap',
                          paddingRight: '32px'
                        } 
                      }}
                      secondaryTypographyProps={{ 
                        style: { 
                          textOverflow: 'ellipsis', 
                          overflow: 'hidden', 
                          whiteSpace: 'nowrap',
                          paddingRight: '32px'
                        } 
                      }}
                    />
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </React.Fragment>
        ))}
      </List>
    </Paper>
  </>
);

export default DrawerContent; 