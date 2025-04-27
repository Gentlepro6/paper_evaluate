import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  CircularProgress,
  Alert,
} from '@mui/material';
import { UploadFile as UploadIcon, Delete as DeleteIcon } from '@mui/icons-material';
import axios from '../utils/axios';

function KnowledgeBase() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploading, setUploading] = useState(false);

  // 获取知识库文件列表
  const fetchFiles = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get('/api/knowledge');
      const files = response.data.files || [];
      console.log('获取到的文件列表:', files);
      setFiles(files);
    } catch (err) {
      console.error('获取知识库列表失败:', err);
      setError('获取知识库列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

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
          const response = await axios.post('/api/knowledge/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Accept': 'application/json',
            },
            transformRequest: [(data) => data],
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

      // 刷新文件列表
      if (successCount > 0) {
        fetchFiles();
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
    if (!window.confirm('确定要删除这个文件吗？')) {
      return;
    }

    try {
      setError('');
      setSuccess('');
      const response = await axios.delete(`/api/knowledge/${fileId}`);
      console.log('删除文件成功:', response.data);
      setSuccess('文件删除成功');
      fetchFiles();
    } catch (err) {
      console.error('删除文件失败:', err);
      setError(err.response?.data?.detail || '删除文件失败');
    }
  };

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h5" gutterBottom>
        知识库管理
      </Typography>

      <Box sx={{ mb: 3 }}>
        <input
          type="file"
          accept=".pdf,.doc,.docx"
          style={{ display: 'none' }}
          id="knowledge-upload"
          onChange={handleFileChange}
          multiple
        />
        <label htmlFor="knowledge-upload">
          <Button
            variant="contained"
            component="span"
            startIcon={<UploadIcon />}
            disabled={uploading}
          >
            选择文件
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
      </Box>

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

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <List sx={{ mt: 2 }}>
          {files.map((file) => (
            <ListItem key={file.id}>
              <ListItemText
                primary={file.title}
                secondary={`上传时间: ${new Date(file.created_at).toLocaleString('zh-CN')}`}
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
      )}

      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          说明
        </Typography>
        <Typography variant="body1">
          支持批量上传 PDF、DOC、DOCX 格式的文件。
        </Typography>
      </Box>
    </Paper>
  );
}

export default KnowledgeBase;
