import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Check as CheckIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import axios from '../utils/axios';

function ModelManagement() {
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [serverUrl, setServerUrl] = useState('http://localhost:11434');
  const [temperature, setTemperature] = useState(0.3);
  const [maxTokens, setMaxTokens] = useState(2000);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [testing, setTesting] = useState(false);

  // 获取配置
  const fetchConfig = async () => {
    try {
      const response = await axios.get('/api/models/config');
      if (response.data && response.data.config) {
        const config = response.data.config;
        setServerUrl(config.server_url || 'http://localhost:11434');
        if (config.default_model) {
          setSelectedModel(config.default_model);
        }
        setTemperature(config.temperature || 0.3);
        setMaxTokens(config.max_tokens || 2000);
      }
    } catch (err) {
      console.error('获取配置失败:', err);
    }
  };

  // 获取模型列表
  const fetchModels = async () => {
    setLoading(true);
    setError('');
    try {
      console.log('开始获取模型列表...');
      const response = await axios.get('/api/models', {
        timeout: 30000 // 增加超时时间到30秒
      });
      
      console.log('获取到的响应:', response);
      
      if (!response.data) {
        throw new Error('服务器返回的数据为空');
      }
      
      const responseData = response.data;
      
      if (responseData.error) {
        console.error('服务器错误:', responseData.error);
        throw new Error(`服务器错误: ${responseData.error}`);
      }
      
      if (!responseData.models || !Array.isArray(responseData.models)) {
        console.error('无效的模型数据格式:', responseData);
        throw new Error('服务器返回的模型数据格式无效');
      }
      
      // 直接使用服务器返回的模型列表
      const processedModels = responseData.models.filter(model => model && model.model);
      
      console.log('处理后的模型列表:', processedModels);
      setModels(processedModels);
      
      if (processedModels.length > 0) {
        // 检查当前选中的模型是否在列表中
        const modelExists = processedModels.some(model => model.model === selectedModel);
        
        if (!selectedModel || !modelExists) {
          console.log('设置默认选中的模型:', processedModels[0].model);
          setSelectedModel(processedModels[0].model);
        }
      } else {
        console.warn('没有可用的模型');
        setError('未找到可用的模型');
        setSelectedModel('');
      }

    } catch (err) {
      console.error('获取模型列表错误:', err);
      if (err.code === 'ECONNABORTED') {
        setError('请求超时，请检查Ollama服务是否运行');
      } else if (err.response) {
        console.error('错误响应:', err.response.data);
        setError(`服务器错误: ${err.response.data.detail || err.response.statusText}`);
      } else {
        setError(`网络错误: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchModels();
  }, []);

  // 测试模型连接
  const testModel = async () => {
    if (!selectedModel) {
      setError('请选择模型');
      return;
    }

    setTesting(true);
    setError('');
    setSuccess('');
    try {
      console.log('发送测试请求:', {
        model_name: selectedModel,
        server_url: serverUrl
      });
      
      const response = await axios.post('/api/models/test', {
        model_name: selectedModel,
        server_url: serverUrl
      });
      
      console.log('测试响应:', response.data);
      setSuccess('模型连接测试成功！');
    } catch (err) {
      console.error('测试失败:', err);
      console.error('错误响应:', err.response);
      console.error('错误数据:', err.response?.data);
      
      if (err.response?.data?.detail) {
        setError(`测试失败: ${err.response.data.detail}`);
      } else if (err.response?.status === 404) {
        setError('测试失败: API端点不存在');
      } else if (err.code === 'ECONNABORTED') {
        setError('测试失败: 请求超时');
      } else if (!err.response) {
        setError('测试失败: 无法连接到服务器');
      } else {
        setError(`测试失败: ${err.message}`);
      }
    } finally {
      setTesting(false);
    }
  };

  // 保存配置
  const saveConfig = async () => {
    if (!selectedModel) {
      setError('请选择模型');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const response = await axios.post('/api/models/config', {
        server_url: serverUrl,
        default_model: selectedModel,
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens)
      });
      
      if (response.data && response.data.config) {
        const config = response.data.config;
        setServerUrl(config.server_url || serverUrl);
        setSelectedModel(config.default_model || selectedModel);
        setTemperature(config.temperature || temperature);
        setMaxTokens(config.max_tokens || maxTokens);
      }
      
      setSuccess('配置保存成功！');
      // 重新加载模型列表
      await fetchModels();
    } catch (err) {
      console.error('保存配置失败:', err);
      setError('配置保存失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h5" gutterBottom>
        模型管理
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
        <TextField
          fullWidth
          label="Ollama服务器地址"
          value={serverUrl}
          onChange={(e) => setServerUrl(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchModels}
          disabled={loading}
          sx={{ mb: 2 }}
        >
          刷新模型列表
        </Button>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ width: '100%' }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>选择模型</InputLabel>
              <Select
                value={selectedModel}
                label="选择模型"
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                {models.map((model) => (
                  <MenuItem key={model.model} value={model.model}>
                    {model.name} {model.size > 0 ? `(${(model.size / 1024 / 1024 / 1024).toFixed(2)} GB)` : ''}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="温度参数"
              type="number"
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
              inputProps={{ min: 0, max: 1, step: 0.1 }}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="最大Token数"
              type="number"
              value={maxTokens}
              onChange={(e) => setMaxTokens(e.target.value)}
              inputProps={{ min: 100, max: 4096, step: 100 }}
              sx={{ mb: 2 }}
            />
          </Box>
        )}

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={testModel}
            disabled={!selectedModel || testing}
            startIcon={testing ? <CircularProgress size={20} /> : <CheckIcon />}
          >
            测试连接
          </Button>

          <Button
            variant="contained"
            onClick={saveConfig}
            disabled={!selectedModel || loading}
          >
            保存配置
          </Button>
        </Box>
      </Box>

      <Typography variant="h6" gutterBottom>
        说明
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        1. 请确保Ollama服务正在运行
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        2. 服务器地址默认为http://localhost:11434
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        3. 建议使用性能较好的模型以获得更好的评价效果
      </Typography>
    </Paper>
  );
}

export default ModelManagement;
