import React, { useState } from 'react';
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
  CircularProgress
} from '@mui/material';
import { Upload as UploadIcon } from '@mui/icons-material';
import axios from 'axios';

function PaperUpload() {
  const [file, setFile] = useState(null);
  const [paperType, setPaperType] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      const fileType = selectedFile.name.toLowerCase();
      if (!fileType.endsWith('.pdf') && !fileType.endsWith('.doc') && !fileType.endsWith('.docx')) {
        setError('只支持 PDF、DOC、DOCX 格式的文件');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file || !paperType) {
      setError('请选择文件和论文类型');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await axios.post(
        `/api/papers/upload/${paperType}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setSuccess('论文上传成功！');
      setFile(null);
      setPaperType('');
    } catch (err) {
      setError(err.response?.data?.detail || '上传失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h5" gutterBottom>
        上传论文
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

      <Box sx={{ mb: 3 }}>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>论文类型</InputLabel>
          <Select
            value={paperType}
            label="论文类型"
            onChange={(e) => setPaperType(e.target.value)}
          >
            <MenuItem value="undergraduate">本科论文</MenuItem>
            <MenuItem value="master">硕士论文</MenuItem>
            <MenuItem value="phd">博士论文</MenuItem>
          </Select>
        </FormControl>

        <Button
          variant="outlined"
          component="label"
          startIcon={<UploadIcon />}
          sx={{ mb: 2 }}
        >
          选择文件
          <input
            type="file"
            hidden
            accept=".pdf,.doc,.docx"
            onChange={handleFileChange}
          />
        </Button>

        {file && (
          <Typography variant="body2" sx={{ mb: 2 }}>
            已选择文件: {file.name}
          </Typography>
        )}

        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={!file || !paperType || loading}
          sx={{ mt: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : '上传论文'}
        </Button>
      </Box>
    </Paper>
  );
}

export default PaperUpload;
