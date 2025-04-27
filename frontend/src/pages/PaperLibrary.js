import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import { Upload as UploadIcon, Delete as DeleteIcon } from '@mui/icons-material';
import axios from '../utils/axios';

function PaperLibrary() {
  const [activeTab, setActiveTab] = useState('undergraduate');
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploading, setUploading] = useState(false);

  // 获取论文列表
  const fetchPapers = async () => {
    setLoading(true);
    setError('');
    try {
      console.log('开始获取论文列表，类型:', activeTab);
      const response = await axios.get(`/api/papers/${activeTab}`);
      console.log('获取到的论文列表:', response.data);
      setFiles(response.data.papers || []);
    } catch (err) {
      console.error('获取论文列表失败:', err);
      setError(err.response?.data?.detail || '获取论文列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPapers();
  }, [activeTab]);

  const handleFileChange = async (event) => {
    const selectedFiles = Array.from(event.target.files);
    if (selectedFiles.length === 0) return;

    // 验证文件类型
    const invalidFiles = selectedFiles.filter(file => {
      const fileType = file.name.toLowerCase();
      return !fileType.endsWith('.pdf') && !fileType.endsWith('.doc') && !fileType.endsWith('.docx');
    });

    if (invalidFiles.length > 0) {
      setError(`以下文件格式不支持: ${invalidFiles.map(f => f.name).join(', ')}`);
      event.target.value = '';
      return;
    }

    setUploading(true);
    setError('');
    setSuccess('');

    // 记录上传进度
    const totalFiles = selectedFiles.length;
    let successCount = 0;
    let failedFiles = [];

    try {
      // 使用 Promise.all 并行上传文件
      await Promise.all(selectedFiles.map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        try {
          console.log(`开始上传文件: ${file.name}`);
          const response = await axios.post(`/api/papers/upload/${activeTab}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (progressEvent) => {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              console.log(`${file.name} 上传进度: ${percentCompleted}%`);
            }
          });
          console.log(`${file.name} 上传成功:`, response.data);
          successCount++;
        } catch (err) {
          console.error(`${file.name} 上传失败:`, err);
          failedFiles.push({ name: file.name, error: err.response?.data?.detail || '上传失败' });
        }
      }));

      // 显示上传结果
      if (successCount === totalFiles) {
        setSuccess(`所有 ${totalFiles} 个文件上传成功！`);
      } else if (successCount > 0) {
        setSuccess(`成功上传 ${successCount} 个文件`);
        setError(`失败 ${failedFiles.length} 个文件: ${failedFiles.map(f => `${f.name} (${f.error})`).join(', ')}`);
      } else {
        setError(`所有文件上传失败: ${failedFiles.map(f => `${f.name} (${f.error})`).join(', ')}`);
      }

      // 刷新论文列表
      if (successCount > 0) {
        fetchPapers();
      }
    } catch (err) {
      console.error('批量上传错误:', err);
      setError('批量上传过程中发生错误');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const handleDelete = async (fileId) => {
    try {
      await axios.delete(`/api/papers/${activeTab}/${fileId}`);
      setSuccess('论文删除成功');
      fetchPapers();
    } catch (err) {
      console.error('删除论文失败:', err);
      setError(err.response?.data?.detail || '删除失败，请重试');
    }
  };

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h5" gutterBottom>
        论文库管理
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Tabs
        value={activeTab}
        onChange={(e, newValue) => setActiveTab(newValue)}
        sx={{ mb: 3 }}
      >
        <Tab label="本科论文" value="undergraduate" />
        <Tab label="硕士论文" value="master" />
        <Tab label="博士论文" value="phd" />
      </Tabs>

      <Box sx={{ mb: 3 }}>
        <input
          type="file"
          accept=".pdf,.doc,.docx"
          style={{ display: 'none' }}
          id="paper-upload"
          onChange={handleFileChange}
          multiple
        />
        <label htmlFor="paper-upload">
          <Button
            variant="contained"
            component="span"
            startIcon={<UploadIcon />}
            disabled={uploading}
          >
            选择论文
          </Button>
        </label>
        {uploading && (
          <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ ml: 1 }}>
              正在上传...
            </Typography>
          </Box>
        )}

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        ) : success ? (
          <Alert severity="success" sx={{ mt: 2 }}>
            {success}
          </Alert>
        ) : null}

        <List>
          {files.map((file) => (
            <ListItem key={file.id} divider>
              <ListItemText
                primary={file.title}
                secondary={`上传时间：${new Date(file.created_at.replace(' ', 'T')).toLocaleString('zh-CN')}`}
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleDelete(file.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </Box>

      <Typography variant="h6" gutterBottom>
        说明
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        1. 支持上传PDF、DOC、DOCX格式的论文
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        2. 系统会自动对上传的论文进行文本提取和向量化处理
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        3. 分类上传有助于提高评价的准确性
      </Typography>
    </Paper>
  );
}

export default PaperLibrary;
