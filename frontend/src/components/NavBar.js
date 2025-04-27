import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

function NavBar() {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          学术论文评价系统
        </Typography>
        <Box>
          <Button color="inherit" component={RouterLink} to="/">
            论文评价
          </Button>
          <Button color="inherit" component={RouterLink} to="/knowledge">
            知识库
          </Button>
          <Button color="inherit" component={RouterLink} to="/library">
            论文库
          </Button>
          <Button color="inherit" component={RouterLink} to="/model">
            模型管理
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default NavBar;
