import React, { useEffect, useState } from 'react';
import { Table, Button, Tag, message, Modal } from 'antd';
import { applications } from '../services/api';
import { Application } from '../types';

const ApplicationList: React.FC = () => {
  const [list, setList] = useState<Application[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const res = await applications.list();
      console.log('Applications response:', res);
      setList(res.data.applications || []);
    } catch (error) {
      console.error('Failed to fetch applications:', error);
      message.error('加载投递记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  // 取消投递
  const handleCancelApplication = (applicationId: number, jobTitle: string) => {
    Modal.confirm({
      title: '确认取消投递',
      content: `确定要取消"${jobTitle}"的投递吗？此操作不可恢复。`,
      okText: '确认取消',
      cancelText: '暂不取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          setLoading(true);
          // 调用后端API更新状态为已取消（或删除记录）
          // 这里假设使用更新状态的接口，将状态改为 CANCELLED
          await applications.updateStatus(applicationId, 'CANCELLED');
          message.success('已取消投递');
          fetchApplications(); // 刷新列表
        } catch (error) {
          console.error('Failed to cancel application:', error);
          message.error('取消投递失败');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 简化状态显示
  const getSimplifiedStatus = (record: Application) => {
    const status = record.status;
    const scoreJson = record.score_json;
    
    // 调试日志
    console.log('状态判断:', { 
      id: record.id, 
      status, 
      hasScoreJson: !!scoreJson,
      scoreJson 
    });
    
    // 已取消状态
    if (status === 'CANCELLED') {
      return { text: '已取消', color: 'default' };
    }
    
    // 已拒绝
    if (status === 'REJECTED') {
      return { text: '简历评估未通过', color: 'error' };
    }
    
    // 已通过状态（最终通过）
    if (status === 'PASSED' || status === 'NEXT_ROUND') {
      return { text: '简历评估通过', color: 'success' };
    }
    
    // 已评分或题包已生成 - 根据分数判断
    // SCORED: 已评分
    // QUESTIONS_READY: 题包已生成（说明已评分且通过）
    if (status === 'SCORED' || status === 'QUESTIONS_READY') {
      if (scoreJson) {
        // 尝试多种可能的分数字段名
        const score = scoreJson.total_score || 
                     scoreJson.score || 
                     scoreJson.overall_score || 
                     (typeof scoreJson === 'number' ? scoreJson : 0);
        const threshold = 60; // 阈值60分
        
        console.log('分数判断:', { score, threshold, result: score >= threshold });
        
        if (score >= threshold) {
          return { text: '简历评估通过', color: 'success' };
        } else {
          return { text: '简历评估未通过', color: 'error' };
        }
      } else {
        // 如果状态是 QUESTIONS_READY 但没有 scoreJson，说明已通过（因为只有通过才会生成题包）
        if (status === 'QUESTIONS_READY') {
          return { text: '简历评估通过', color: 'success' };
        }
        // SCORED 但没有 scoreJson，可能是数据异常，显示评估中
        return { text: '评估中', color: 'processing' };
      }
    }
    
    // 其他状态 - 评估中（PARSING, PARSED, SCORING, HUMAN_REVIEW等）
    return { text: '评估中', color: 'processing' };
  };

  const columns = [
    { 
      title: '投递ID', 
      dataIndex: 'id', 
      key: 'id',
      width: 100
    },
    { 
      title: '职位', 
      dataIndex: 'job_title', 
      key: 'job_title',
      width: 200
    },
    { 
      title: '状态', 
      dataIndex: 'status', 
      key: 'status',
      width: 150,
      render: (_: string, record: Application) => {
        const statusInfo = getSimplifiedStatus(record);
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>;
      }
    },
    { 
      title: '投递时间', 
      dataIndex: 'created_at', 
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Application) => {
        // 只有评估中或已通过/未通过的可以取消
        const canCancel = !['CANCELLED'].includes(record.status);
        
        return canCancel ? (
          <Button 
            danger 
            size="small"
            onClick={() => handleCancelApplication(record.id, record.job_title)}
          >
            取消投递
          </Button>
        ) : (
          <span style={{ color: '#999' }}>已取消</span>
        );
      },
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <h2>我的投递</h2>
      <Table 
        dataSource={list} 
        columns={columns} 
        rowKey="id" 
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};

export default ApplicationList;
