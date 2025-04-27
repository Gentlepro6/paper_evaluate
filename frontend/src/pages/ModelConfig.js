import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Alert,
  CircularProgress,
  Box
} from '@mui/material';
import { Check as CheckIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import axios from 'axios';

function ModelConfig() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [testing, setTesting] = useState(false);
  const [config, setConfig] = useState({
    server_url: '',
    default_model: '',
    temperature: 0.3,
    max_tokens: 2000
  });
  const [isDefault, setIsDefault] = useState(true);

  // 获取模型配置
  const fetchConfig = async () => {
    try {
      const response = await axios.get('/api/models/config');
      if (response.data.status === 'success') {
        setConfig(response.data.config);
        setIsDefault(response.data.is_default);
      }
    } catch (err) {
      setError('获取模型配置失败');
    }
  };

  // 保存模型配置
  const saveConfig = async () => {
    try {
      const response = await axios.post('/api/models/config', config);
      if (response.data.status === 'success') {
        setSuccess('配置保存成功');
        setIsDefault(false);
      }
    } catch (err) {
      setError('保存配置失败');
    }
  };

  // 获取模型列表
  const fetchModels = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get('/api/models');
      setModels(response.data.models || []);
    } catch (err) {
      setError('获取模型列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 测试模型
  const testModel = async (modelName) => {
    setTesting(true);
    setError('');
    setSuccess('');
    try {
      await axios.post('/api/models/test', { model_name: modelName });
      setSuccess('模型测试成功！');
    } catch (err) {
      setError('模型测试失败');
    } finally {
      setTesting(false);
    }
  };

  useEffect(() => {
    fetchModels();
    fetchConfig();
  }, []);

  return (
    <Paper sx={{ p: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">
          模型配置
        </Typography>
        <Button
          variant="contained"
          onClick={saveConfig}
          disabled={loading}
        >
          保存配置
        </Button>
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

      <Box sx={{ mb: 3 }}>
        <Button
          variant="contained"
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
          <List>
            {models.map((model) => (
              <ListItem key={model.name} divider>
                <ListItemText
                  primary={model.name}
                  secondary={`大小: ${(model.size / 1024 / 1024 / 1024).toFixed(2)} GB`}
                />
                <ListItemSecondaryAction>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => testModel(model.name)}
                    disabled={testing}
                    startIcon={testing ? <CircularProgress size={20} /> : <CheckIcon />}
                  >
                    测试
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          服务器配置
        </Typography>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            服务器地址
          </Typography>
          <input
            type="text"
            value={config.server_url}
            onChange={(e) => setConfig({ ...config, server_url: e.target.value })}
            placeholder="例如：http://localhost:11434"
            style={{ width: '100%', padding: '8px' }}
          />
        </Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            默认模型
          </Typography>
          <select
            value={config.default_model}
            onChange={(e) => setConfig({ ...config, default_model: e.target.value })}
            style={{ width: '100%', padding: '8px' }}
          >
            <option value="">请选择默认模型</option>
            {models.map((model) => (
              <option key={model.name} value={model.name}>{model.name}</option>
            ))}
          </select>
        </Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            温度
          </Typography>
          <input
            type="number"
            value={config.temperature}
            onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
            min="0"
            max="1"
            step="0.1"
            style={{ width: '100%', padding: '8px' }}
          />
        </Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            最大输出长度
          </Typography>
          <input
            type="number"
            value={config.max_tokens}
            onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
            min="100"
            max="4096"
            step="100"
            style={{ width: '100%', padding: '8px' }}
          />
        </Box>
      </Box>

      <Typography variant="h6" gutterBottom>
        模型说明
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        1. 系统使用本地部署的Ollama模型进行论文评价
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        2. 请确保Ollama服务正在运行，并且已安装所需模型
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        3. 建议使用性能较好的模型（如llama2）以获得更好的评价效果
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        4. 温度范围为0-1，越大输出越随机，建议设置为0.3
      </Typography>
    </Paper>
  );
}

export default ModelConfig;
