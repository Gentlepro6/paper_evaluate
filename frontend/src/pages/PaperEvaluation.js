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
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Grid,
} from '@mui/material';
import { 
  Upload as UploadIcon, 
  GetApp as GetAppIcon,
  OpenInNew as OpenInNewIcon,
  Save as SaveIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import axios from '../utils/axios';


function PaperEvaluation() {
  const [file, setFile] = useState(null);
  const [paperType, setPaperType] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [evaluations, setEvaluations] = useState([]);
  const [selectedEvaluations, setSelectedEvaluations] = useState([]);
  const [paperCounts, setPaperCounts] = useState({
    undergraduate: 0,
    master: 0,
    phd: 0,
    knowledge_base: 0
  });
  const minRequiredPapers = 5;

  const handleFileChange = async (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      // 检查文件类型
      const fileType = selectedFile.name.toLowerCase();
      if (!fileType.endsWith('.pdf') && !fileType.endsWith('.doc') && !fileType.endsWith('.docx')) {
        setError('只支持 PDF、DOC、DOCX 格式的文件');
        setFile(null);
        localStorage.removeItem('selectedFileName');
        return;
      }

      // 检查文件大小，限制为10MB
      const maxSize = 10 * 1024 * 1024; // 10MB in bytes
      if (selectedFile.size > maxSize) {
        setError('文件太大，请选择小于10MB的文件');
        setFile(null);
        localStorage.removeItem('selectedFileName');
        return;
      }

      try {
        // 上传到临时目录
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        const tempUploadResponse = await axios.post('/api/papers/upload-temp', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Accept': 'application/json',
          },
          transformRequest: [(data) => data],
          timeout: 30000,
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log('上传进度:', percentCompleted, '%');
          }
        });

        console.log('临时上传响应:', tempUploadResponse);

        if (!tempUploadResponse?.data) {
          throw new Error('临时上传响应为空');
        }

        setFile(selectedFile);
        localStorage.setItem('selectedFileName', selectedFile.name);
        setError('');
        setSuccess('文件已上传到临时目录');
      } catch (error) {
        console.error('上传到临时目录失败:', error);
        setError(`上传失败: ${error.response?.data?.detail || error.message}`);
        setFile(null);
        localStorage.removeItem('selectedFileName');
      }
    }
  };

  // 获取论文数量
  const fetchPaperCounts = async () => {
    try {
      const response = await axios.get('/api/papers/counts');
      setPaperCounts(response.data);
    } catch (error) {
      console.error('获取论文数量失败:', error);
      setError('获取论文数量失败');
    }
  };

  // 获取评价历史
  const fetchEvaluationHistory = async () => {
    try {
      const response = await axios.get('/api/papers/evaluations');
      console.log('评价历史响应:', response.data);
      if (response.data && Array.isArray(response.data.evaluations)) {
        const formattedEvaluations = response.data.evaluations.map(evaluation => ({
          id: evaluation.id,
          paperId: evaluation.paperId,
          fileName: evaluation.fileName,
          title: evaluation.title,
          paperType: evaluation.paperType,
          modelName: evaluation.modelName,
          score: parseFloat(evaluation.score),
          comments: evaluation.comments,
          timestamp: evaluation.timestamp
        }));
        console.log('格式化后的评价:', formattedEvaluations);
        setEvaluations(formattedEvaluations);
      } else {
        console.error('评价历史数据格式错误:', response.data);
      }
    } catch (error) {
      console.error('获取评价历史失败:', error);
      setError('获取评价历史失败');
    }
  };

  // 组件加载时获取论文数量和评价历史
  React.useEffect(() => {
    fetchPaperCounts();
    fetchEvaluationHistory();
    
    // 恢复选择的论文类型
    const savedPaperType = localStorage.getItem('selectedPaperType');
    if (savedPaperType) {
      setPaperType(savedPaperType);
    }

    // 恢复选择的文件名
    const savedFileName = localStorage.getItem('selectedFileName');
    if (savedFileName) {
      // 创建一个文件对象
      const file = new File([""], savedFileName, {
        type: savedFileName.endsWith('.pdf') ? 'application/pdf' :
              savedFileName.endsWith('.doc') ? 'application/msword' :
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      setFile(file);
    }
  }, []);



  // 当选择的论文类型变化时，保存到 localStorage
  React.useEffect(() => {
    if (paperType) {
      localStorage.setItem('selectedPaperType', paperType);
    }
  }, [paperType]);

  // 检查论文数量是否满足要求
  const checkPaperCounts = () => {
    if (!paperType) return false;
    return paperCounts.knowledge_base >= minRequiredPapers && 
           paperCounts[paperType] >= minRequiredPapers;
  };

  // 获取提示信息
  const getCountWarning = () => {
    if (!paperType) return '';
    const warnings = [];
    if (paperCounts.knowledge_base < minRequiredPapers) {
      warnings.push(`知识库中需要至少 ${minRequiredPapers} 篇文档`);
    }
    if (paperCounts[paperType] < minRequiredPapers) {
      warnings.push(`${paperType === 'undergraduate' ? '本科' : paperType === 'master' ? '硕士' : '博士'}论文库中需要至少 ${minRequiredPapers} 篇文档`);
    }
    return warnings.join('、');
  };

  const handleEvaluate = async () => {
    if (!file) {
      setError('请选择要评价的论文文件');
      return;
    }
    if (!paperType) {
      setError('请选择论文类型');
      return;
    }



    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // 第一步：上传论文到临时目录
      const formData = new FormData();
      formData.append('file', file);
      console.log('开始上传论文到临时目录:', file.name);
      
      const uploadResponse = await axios.post('/api/papers/upload-temp', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Accept': 'application/json',
        },
        transformRequest: [(data) => data],
        timeout: 30000,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log('上传进度:', percentCompleted, '%');
        }
      });

      console.log('上传响应:', uploadResponse);

      const evaluateResponse = await axios.post(
        `/api/papers/evaluate/${paperType}`,
        {
          model_name: null,  // 使用系统默认模型
          temperature: null,  // 使用系统默认参数
          max_tokens: null,  // 使用系统默认参数
          filename: file.name  // 添加文件名参数，确保评价正确的论文
        },
        {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 600000  // 10分钟超时
        }
      );

      console.log('评价响应:', evaluateResponse);

      if (!evaluateResponse?.data) {
        throw new Error('评价失败：服务器响应为空');
      }

      const evalResult = evaluateResponse.data;

      // 验证必要字段
      if (!evalResult.id || !evalResult.paper_id || 
          typeof evalResult.score === 'undefined' || 
          !evalResult.comments || !evalResult.paper_title) {
        console.error('评价响应数据:', evaluateResponse.data);
        throw new Error(`评价失败：${evaluateResponse.data.detail || '响应格式不正确'}`);
      }
      
      console.log('评价结果:', evaluateResponse.data);
      setEvaluations(prevEvaluations => [
        ...prevEvaluations,
        {
          id: evalResult.id,
          paperId: evalResult.paper_id,
          fileName: file.name,
          title: evalResult.paper_title,
          paperType: evalResult.paper_type,
          modelName: evalResult.model_name,
          score: parseFloat(evalResult.score),
          comments: evalResult.comments,
          timestamp: new Date().toISOString()
        }
      ]);

      setSuccess(evalResult.message || `论文「${evalResult.paper_title}」评价完成！`);
      fetchPaperCounts(); // 更新论文数量
      setFile(null);
      setPaperType('');
      
    } catch (error) {
      console.error('上传或评价过程出错:', error);
      let errorMessage = error.response?.data?.detail || error.message || '未知错误';
      setError(`操作失败：${errorMessage}`);
      if (error.response?.status === 413) {
        setError('文件太大，请选择小于10MB的文件');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (selectedOnly = false) => {
    const evaluationsToExport = selectedOnly ? 
      evaluations.filter(evaluation => selectedEvaluations.includes(evaluation.id)) :
      evaluations;
    
    // 创建HTML内容
    let htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>论文评价结果</title>
        <style>
          body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; }
          h1 { text-align: center; font-size: 24px; margin-bottom: 20px; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
          th { background-color: #f2f2f2; padding: 10px; text-align: center; font-weight: bold; border: 1px solid #ddd; }
          td { padding: 8px; border: 1px solid #ddd; vertical-align: top; }
          .filename { width: 15%; }
          .score { width: 10%; text-align: center; font-weight: bold; color: red; }
          .comments { width: 60%; white-space: pre-wrap; }
          .timestamp { width: 15%; }
          .no-data { text-align: center; padding: 20px; }
        </style>
      </head>
      <body>
        <h1>论文评价结果</h1>
        <table>
          <thead>
            <tr>
              <th class="filename">文件名称</th>
              <th class="score">论文得分</th>
              <th class="comments">评价意见</th>
              <th class="timestamp">评价时间</th>
            </tr>
          </thead>
          <tbody>
    `;

    // 添加评价数据行
    if (evaluationsToExport.length > 0) {
      evaluationsToExport.forEach(evaluation => {
        // 格式化时间
        const timestamp = new Date(evaluation.timestamp);
        const formattedTime = timestamp.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
        
        // 处理评价意见中的特殊字符，保留原始格式
        const formattedComments = evaluation.comments
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#039;');
        
        // 添加表格行
        htmlContent += `
            <tr>
              <td class="filename">${evaluation.fileName}</td>
              <td class="score">${evaluation.score}</td>
              <td class="comments">${formattedComments}</td>
              <td class="timestamp">${formattedTime}</td>
            </tr>
        `;
      });
    } else {
      htmlContent += `
            <tr>
              <td colspan="4" class="no-data">暂无评价数据</td>
            </tr>
      `;
    }

    // 完成HTML内容
    htmlContent += `
          </tbody>
        </table>
      </body>
      </html>
    `;

    // 创建Blob对象
    const blob = new Blob([htmlContent], { type: 'text/html' });
    
    // 创建下载链接并触发下载
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `论文评价结果_${new Date().toLocaleDateString()}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // 打开选中的评价记录文件
  const handleOpenSelected = () => {
    // 创建一个文件选择器
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.html,.rtf'; // 支持HTML和RTF格式
    
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        // 读取文件内容并创建新窗口显示
        const reader = new FileReader();
        reader.onload = (event) => {
          // 创建一个新窗口并写入HTML内容
          const newWindow = window.open('', '_blank');
          if (newWindow) {
            newWindow.document.write(event.target.result);
            newWindow.document.close();
          } else {
            alert('无法打开新窗口，请检查您的浏览器设置。');
          }
        };
        reader.readAsText(file);
      }
    };
    
    input.click();
  };

  // 清空评价历史
  const handleClearHistory = async () => {
    if (window.confirm('确定要清空评价历史吗？')) {
      try {
        await axios.delete(`/api/evaluations?paper_id=${evaluations[0]?.paperId}`);
        setEvaluations([]);
        setSelectedEvaluations([]);
        setSuccess('评价历史已清空');
      } catch (error) {
        setError(`清空评价历史失败: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  return (
    <div>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h5" sx={{ mb: 1 }}>
          论文评价
        </Typography>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          注意：评价论文需要论文库和知识库各至少有 5 个文档作为参考。
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {paperType && !checkPaperCounts() && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {getCountWarning()}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <Box sx={{ mb: 1 }}>
          <Grid container spacing={2} alignItems="flex-end" justifyContent="space-between">
            <Grid item container spacing={2} xs={12} md={8} alignItems="flex-end">
              <Grid item>
                <FormControl sx={{ minWidth: 200 }}>
                  <InputLabel id="paper-type-label">论文类型</InputLabel>
                  <Select
                    labelId="paper-type-label"
                    value={paperType}
                    label="论文类型"
                    onChange={(e) => {
                      setPaperType(e.target.value);
                      setError('');
                    }}
                    size="small"
                    sx={{
                      minHeight: '36.5px'  // 与按钮高度一致
                    }}
                  >
                    <MenuItem value="undergraduate">本科论文</MenuItem>
                    <MenuItem value="master">硕士论文</MenuItem>
                    <MenuItem value="phd">博士论文</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item>
                <Button
                  variant="outlined"
                  component="label"
                  startIcon={<UploadIcon />}
                >
                  选择文件
                  <input
                    type="file"
                    hidden
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileChange}
                  />
                </Button>
              </Grid>

              <Grid item>
                <Button
                  variant="contained"
                  onClick={handleEvaluate}
                  disabled={!file || !paperType || loading || !checkPaperCounts()}
                >
                  {loading ? <CircularProgress size={24} /> : '开始评价'}
                </Button>
              </Grid>

              <Grid item>
                <Button
                  variant="outlined"
                  onClick={handleExport}
                  disabled={evaluations.length === 0}
                  startIcon={<GetAppIcon />}
                >
                  导出评价结果
                </Button>
              </Grid>
            </Grid>
            
            {/* 右侧操作按钮 */}
            <Grid item container spacing={1} xs={12} md={4} alignItems="flex-end" justifyContent="flex-end">
              <Grid item>
                <Button
                  variant="outlined"
                  onClick={handleOpenSelected}
                  disabled={false} /* 始终可用，便于打开之前导出的评价结果 */
                  startIcon={<OpenInNewIcon />}
                  size="small"
                >
                  打开选中
                </Button>
              </Grid>
              <Grid item>
                <Button
                  variant="outlined"
                  onClick={() => handleExport(true)}
                  disabled={selectedEvaluations.length === 0}
                  startIcon={<SaveIcon />}
                  size="small"
                >
                  导出选中
                </Button>
              </Grid>
              <Grid item>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={handleClearHistory}
                  disabled={evaluations.length === 0}
                  startIcon={<DeleteIcon />}
                  size="small"
                >
                  清空列表
                </Button>
              </Grid>
            </Grid>
          </Grid>

          {file && (
            <Typography variant="body2" sx={{ mt: 2 }}>
              已选择文件: {file.name}
            </Typography>
          )}
        </Box>
      </Paper>

      {/* 评价结果列表 */}
      <Paper sx={{ p: 2, mt: 0.5 }}>
        <Typography variant="h5" sx={{ mb: 1 }}>
          评价结果
        </Typography>

        {evaluations.length > 0 ? (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox">
                    <input
                      type="checkbox"
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedEvaluations(evaluations.map(evaluation => evaluation.id));
                        } else {
                          setSelectedEvaluations([]);
                        }
                      }}
                      checked={selectedEvaluations.length === evaluations.length}
                    />
                  </TableCell>
                  <TableCell width="14%">文件名称</TableCell>
                  <TableCell width="10%">论文得分</TableCell>
                  <TableCell width="61%">论文评语</TableCell>
                  <TableCell width="15%" align="right">
                    评价时间
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[...evaluations].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).map((evaluation, index) => (
                  <TableRow key={index}>
                    <TableCell padding="checkbox">
                      <input
                        type="checkbox"
                        checked={selectedEvaluations.includes(evaluation.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedEvaluations([...selectedEvaluations, evaluation.id]);
                          } else {
                            setSelectedEvaluations(selectedEvaluations.filter(id => id !== evaluation.id));
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell sx={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{evaluation.fileName}</TableCell>
                    <TableCell>{evaluation.score}</TableCell>
                    <TableCell style={{ whiteSpace: 'pre-wrap', minWidth: '400px' }}>
                      {evaluation.comments}
                    </TableCell>
                    <TableCell align="right">{new Date(evaluation.timestamp).toLocaleString('zh-CN')}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography variant="body1" color="text.secondary">
            暂无评价记录
          </Typography>
        )}
      </Paper>


    </div>
  );
}

export default PaperEvaluation;
