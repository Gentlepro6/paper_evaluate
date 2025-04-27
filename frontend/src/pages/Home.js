import React from 'react';
import { Typography, Paper, Grid, Card, CardContent, CardActions, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

function Home() {
  const navigate = useNavigate();

  return (
    <div>
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          欢迎使用学术论文评价系统
        </Typography>
        <Typography variant="body1" paragraph>
          本系统使用先进的AI技术，结合本地大语言模型，为学术论文提供专业的评价服务。
        </Typography>
      </Paper>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                论文上传
              </Typography>
              <Typography variant="body2" color="text.secondary">
                支持上传本科、硕士、博士论文，格式包括PDF、DOC、DOCX。
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/upload')}>
                开始上传
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                论文评价
              </Typography>
              <Typography variant="body2" color="text.secondary">
                查看已上传的论文列表，进行评价和分析。
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/papers')}>
                查看论文
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="div">
                模型配置
              </Typography>
              <Typography variant="body2" color="text.secondary">
                配置和管理本地Ollama模型，确保系统正常运行。
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/model')}>
                配置模型
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
}

export default Home;
