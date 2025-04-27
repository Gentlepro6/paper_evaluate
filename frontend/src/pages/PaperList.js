import React, { useState, useEffect, useCallback } from 'react';
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Box
} from '@mui/material';
import axios from 'axios';

function PaperList() {
  const [papers, setPapers] = useState([]);
  const [paperType, setPaperType] = useState('undergraduate');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [evaluationDialog, setEvaluationDialog] = useState(false);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [evaluating, setEvaluating] = useState(false);

  // 获取论文列表
  const fetchPapers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`/api/papers/${paperType}`);
      setPapers(response.data);
    } catch (err) {
      setError('获取论文列表失败');
    } finally {
      setLoading(false);
    }
  }, [paperType]);

  // 评价论文
  const evaluatePaper = async (paperId) => {
    setEvaluating(true);
    try {
      const response = await axios.post(`/api/papers/${paperId}/evaluate`);
      setEvaluation(response.data);
    } catch (err) {
      setError('论文评价失败');
    } finally {
      setEvaluating(false);
    }
  };

  useEffect(() => {
    fetchPapers();
  }, [fetchPapers]);

  const handleEvaluate = (paper) => {
    setSelectedPaper(paper);
    setEvaluation(null);
    setEvaluationDialog(true);
    evaluatePaper(paper.id);
  };

  return (
    <div>
      <Paper sx={{ p: 4, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          论文列表
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <FormControl sx={{ mb: 3, minWidth: 200 }}>
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

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>标题</TableCell>
                  <TableCell>上传时间</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {papers.map((paper) => (
                  <TableRow key={paper.id}>
                    <TableCell>{paper.title}</TableCell>
                    <TableCell>
                      {new Date(paper.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="contained"
                        size="small"
                        onClick={() => handleEvaluate(paper)}
                      >
                        评价
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      <Dialog
        open={evaluationDialog}
        onClose={() => setEvaluationDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          论文评价结果
          {selectedPaper && ` - ${selectedPaper.title}`}
        </DialogTitle>
        <DialogContent>
          {evaluating ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>
                正在评价论文，请稍候...
              </Typography>
            </Box>
          ) : evaluation ? (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                得分：{evaluation.score}
              </Typography>
              <Typography variant="body1" paragraph>
                评语：{evaluation.comments}
              </Typography>
            </Box>
          ) : (
            <Typography color="error">
              评价失败，请重试
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEvaluationDialog(false)}>关闭</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default PaperList;
