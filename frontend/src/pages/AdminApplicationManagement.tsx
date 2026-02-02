import React, { useEffect, useState } from 'react';
import { Table, Tag, Button, Space, Modal, message, Select, Badge, Tooltip, Card, Descriptions } from 'antd';
import { EyeOutlined, FileTextOutlined, DownloadOutlined } from '@ant-design/icons';
import { Application } from '../types';
import request from '../utils/request';
import { applications } from '../services/api';

const { Option } = Select;

const AdminApplicationManagement: React.FC = () => {
  const [list, setList] = useState<Application[]>([]);
  const [loading, setLoading] = useState(false);
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentApp, setCurrentApp] = useState<Application | null>(null);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      // 使用 admin API 获取所有投递
      const res = await request.get('/admin/applications');
      console.log('Admin applications response:', res);
      const appsData = res.data?.items || res.data?.applications || [];
      setList(appsData);
    } catch (error) {
      console.error('Failed to fetch applications:', error);
      message.error('获取投递列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleViewDetail = async (app: Application) => {
    try {
      setLoading(true);
      // 重新从后端获取完整的详情数据
      const res = await request.get(`/admin/applications/${app.id}`);
      console.log('Application detail response:', res);
      if (res.data) {
        setCurrentApp(res.data);
        setDetailVisible(true);
      } else {
        message.error('获取详情失败');
      }
    } catch (error) {
      console.error('Failed to fetch application detail:', error);
      message.error('获取详情失败');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (appId: number, status: string) => {
    try {
      await request.put(`/admin/applications/${appId}/status`, { status });
      message.success('状态更新成功');
      fetchApplications();
    } catch (error) {
      message.error('状态更新失败');
    }
  };

  // 下载简历
  const handleDownloadResume = async (appId: number) => {
    try {
      message.loading({ content: '正在下载简历...', key: 'download' });
      await applications.downloadResume(appId);
      message.success({ content: '下载成功', key: 'download', duration: 2 });
    } catch (error: any) {
      console.error('Failed to download resume:', error);
      message.error({ 
        content: error.message || '下载简历失败', 
        key: 'download',
        duration: 3 
      });
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'PENDING': 'blue',
      'PARSING': 'processing',
      'PARSED': 'cyan',
      'SCORING': 'processing',
      'SCORED': 'geekblue',
      'GENERATING_QUESTIONS': 'processing',
      'QUESTIONS_GENERATED': 'purple',
      'INTERVIEW_SCHEDULED': 'green',
      'INTERVIEW_COMPLETED': 'default',
      'PASSED': 'success',
      'REJECTED': 'error',
      'HUMAN_REVIEW': 'warning',
    };
    return colors[status] || 'default';
  };

  const columns = [
    {
      title: '投递ID',
      dataIndex: 'id', // 改为 id
      key: 'id',
      width: 80,
      fixed: 'left' as const,
    },
    {
      title: '用户ID',
      key: 'user_id',
      width: 80,
      render: (_: any, record: any) => record.user_id || 'N/A',
    },
    {
      title: '候选人邮箱',
      key: 'user_email',
      width: 200,
      render: (_: any, record: any) => {
        // 优先显示 candidate_email 字段
        if (record.candidate_email) {
          return record.candidate_email;
        }
        // 其次显示关联的 user 对象的 email
        if (record.user?.email) {
          return record.user.email;
        }
        // 最后显示 user_id
        return record.user_id ? `User #${record.user_id}` : 'N/A';
      },
    },
    {
      title: '职位',
      dataIndex: 'job_title',
      key: 'job_title',
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 150,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{status}</Tag>
      ),
    },
    {
      title: '投递时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 260,
      fixed: 'right' as const,
      render: (_: any, record: Application) => (
        <Space size="small">
          <Tooltip title="下载简历">
            <Button 
              type="link" 
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownloadResume(record.id)}
            >
              简历
            </Button>
          </Tooltip>
          <Button 
            type="link" 
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Select
            size="small"
            style={{ width: 100 }}
            placeholder="更新状态"
            onChange={(value: string) => handleUpdateStatus(record.id, value)}
          >
            <Option value="HUMAN_REVIEW">人工审核</Option>
            <Option value="INTERVIEW_SCHEDULED">安排面试</Option>
            <Option value="PASSED">通过</Option>
            <Option value="REJECTED">拒绝</Option>
          </Select>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>投递管理</h2>
        <Button onClick={fetchApplications} loading={loading}>
          刷新
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={list}
        rowKey="id" // 改为 id
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="投递详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
        ]}
        width={900}
      >
        {currentApp && (
          <div>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="投递ID">{(currentApp as any).id}</Descriptions.Item>
              <Descriptions.Item label="用户ID">{(currentApp as any).user_id}</Descriptions.Item>
              <Descriptions.Item label="候选人邮箱" span={2}>
                {(currentApp as any).candidate_email || `User #${(currentApp as any).user_id}`}
              </Descriptions.Item>
              <Descriptions.Item label="职位" span={2}>{currentApp.job_title}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={getStatusColor(currentApp.status)}>{currentApp.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="投递时间">
                {new Date(currentApp.created_at).toLocaleString('zh-CN')}
              </Descriptions.Item>
            </Descriptions>
            
            {/* 简历评估打分情况 */}
            {(currentApp as any).score_json && (
              <Card 
                title="📊 大模型简历评估" 
                size="small" 
                style={{ marginTop: 16 }}
                headStyle={{ background: '#f5f5f5' }}
              >
                {(() => {
                  const scoreData = (currentApp as any).score_json;
                  // 使用 overall_score（后端返回的字段）
                  const overallScore = scoreData.overall_score || scoreData.total_score || scoreData.score || 0;
                  const educationScore = scoreData.education_score;
                  const experienceScore = scoreData.experience_score;
                  const skillsScore = scoreData.skills_score;
                  const matchAnalysis = scoreData.match_analysis;
                  const strengths = scoreData.strengths || [];
                  const weaknesses = scoreData.weaknesses || [];
                  const recommendation = scoreData.recommendation || '';
                  
                  return (
                    <div>
                      {/* 总分展示 */}
                      <div style={{ marginBottom: 20, textAlign: 'center' }}>
                        <div style={{ fontSize: 56, fontWeight: 'bold', color: overallScore >= 60 ? '#52c41a' : '#ff4d4f' }}>
                          {overallScore}
                        </div>
                        <div style={{ fontSize: 14, color: '#999', marginTop: 4 }}>总分 (满分100)</div>
                      </div>
                      
                      {/* 各维度得分 */}
                      {(educationScore !== undefined || experienceScore !== undefined || skillsScore !== undefined) && (
                        <div style={{ marginBottom: 20 }}>
                          <div style={{ fontSize: 14, fontWeight: 'bold', marginBottom: 12 }}>各维度得分：</div>
                          {educationScore !== undefined && (
                            <div style={{ marginBottom: 12 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                                <span>教育背景</span>
                                <span style={{ fontWeight: 'bold' }}>{educationScore}分</span>
                              </div>
                              <div style={{ 
                                height: 10, 
                                background: '#f0f0f0', 
                                borderRadius: 5, 
                                overflow: 'hidden' 
                              }}>
                                <div style={{ 
                                  width: `${educationScore}%`, 
                                  height: '100%', 
                                  background: educationScore >= 60 ? '#52c41a' : '#ff4d4f',
                                  transition: 'width 0.3s'
                                }} />
                              </div>
                            </div>
                          )}
                          {experienceScore !== undefined && (
                            <div style={{ marginBottom: 12 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                                <span>工作经验</span>
                                <span style={{ fontWeight: 'bold' }}>{experienceScore}分</span>
                              </div>
                              <div style={{ 
                                height: 10, 
                                background: '#f0f0f0', 
                                borderRadius: 5, 
                                overflow: 'hidden' 
                              }}>
                                <div style={{ 
                                  width: `${experienceScore}%`, 
                                  height: '100%', 
                                  background: experienceScore >= 60 ? '#52c41a' : '#ff4d4f',
                                  transition: 'width 0.3s'
                                }} />
                              </div>
                            </div>
                          )}
                          {skillsScore !== undefined && (
                            <div style={{ marginBottom: 12 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                                <span>技能匹配</span>
                                <span style={{ fontWeight: 'bold' }}>{skillsScore}分</span>
                              </div>
                              <div style={{ 
                                height: 10, 
                                background: '#f0f0f0', 
                                borderRadius: 5, 
                                overflow: 'hidden' 
                              }}>
                                <div style={{ 
                                  width: `${skillsScore}%`, 
                                  height: '100%', 
                                  background: skillsScore >= 60 ? '#52c41a' : '#ff4d4f',
                                  transition: 'width 0.3s'
                                }} />
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* 匹配分析 */}
                      {matchAnalysis && (
                        <div style={{ 
                          marginBottom: 16,
                          padding: 12, 
                          background: '#f0f7ff', 
                          borderRadius: 4,
                          borderLeft: '4px solid #1890ff'
                        }}>
                          <div style={{ fontWeight: 'bold', marginBottom: 8, color: '#1890ff' }}>📋 匹配分析：</div>
                          <div style={{ lineHeight: 1.6, color: '#333' }}>{matchAnalysis}</div>
                        </div>
                      )}
                      
                      {/* 优势 */}
                      {strengths && Array.isArray(strengths) && strengths.length > 0 && (
                        <div style={{ marginBottom: 16 }}>
                          <div style={{ fontWeight: 'bold', marginBottom: 8, color: '#52c41a' }}>✅ 优势：</div>
                          <div>
                            {strengths.map((strength: string, idx: number) => (
                              <Tag key={idx} color="success" style={{ marginBottom: 4 }}>
                                {strength}
                              </Tag>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* 不足 */}
                      {weaknesses && Array.isArray(weaknesses) && weaknesses.length > 0 && (
                        <div style={{ marginBottom: 16 }}>
                          <div style={{ fontWeight: 'bold', marginBottom: 8, color: '#ff4d4f' }}>⚠️ 不足：</div>
                          <div>
                            {weaknesses.map((weakness: string, idx: number) => (
                              <Tag key={idx} color="error" style={{ marginBottom: 4 }}>
                                {weakness}
                              </Tag>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* 推荐建议 */}
                      {recommendation && (
                        <div style={{ 
                          padding: 14, 
                          background: overallScore >= 60 ? '#f6ffed' : '#fff2e8', 
                          borderRadius: 4,
                          borderLeft: `4px solid ${overallScore >= 60 ? '#52c41a' : '#fa8c16'}`
                        }}>
                          <div style={{ fontWeight: 'bold', marginBottom: 8, color: overallScore >= 60 ? '#52c41a' : '#fa8c16' }}>
                            💡 大模型推荐建议：
                          </div>
                          <div style={{ lineHeight: 1.6, color: '#333' }}>{recommendation}</div>
                        </div>
                      )}
                      
                      {/* 显示完整JSON（折叠） */}
                      <details style={{ marginTop: 16 }}>
                        <summary style={{ cursor: 'pointer', color: '#1890ff', fontSize: 12 }}>
                          查看完整评分数据（JSON）
                        </summary>
                        <pre style={{ 
                          background: '#fafafa', 
                          padding: 12, 
                          marginTop: 8,
                          fontSize: 11,
                          maxHeight: 300,
                          overflowY: 'auto',
                          borderRadius: 4,
                          border: '1px solid #e8e8e8'
                        }}>
                          {JSON.stringify(scoreData, null, 2)}
                        </pre>
                      </details>
                    </div>
                  );
                })()}
              </Card>
            )}
            
            {/* 题包展示 */}
            {(() => {
              let questionsData = (currentApp as any).questions_json;
              
              // 如果 questions_json 是字符串，尝试解析
              if (typeof questionsData === 'string') {
                try {
                  questionsData = JSON.parse(questionsData);
                } catch (e) {
                  console.error('Failed to parse questions_json:', e);
                  questionsData = null;
                }
              }
              
              // 提取 questions 数组
              let questions: any[] = [];
              if (questionsData) {
                if (Array.isArray(questionsData)) {
                  questions = questionsData;
                } else if (typeof questionsData === 'object') {
                  questions = questionsData.questions || questionsData.items || questionsData.list || questionsData.data || [];
                }
              }
              
              return questions && questions.length > 0 ? (
                <Card 
                  title={
                    <span>
                      <FileTextOutlined style={{ marginRight: 8 }} />
                      面试题包
                      <Badge 
                        count={questions.length} 
                        style={{ marginLeft: 8 }}
                        showZero={false}
                      />
                    </span>
                  }
                  size="small" 
                  style={{ marginTop: 16 }}
                  headStyle={{ background: '#f5f5f5' }}
                >
                  <div>
                    <div style={{ marginBottom: 16, padding: 8, background: '#f0f7ff', borderRadius: 4 }}>
                      <span style={{ fontWeight: 'bold' }}>题目总数：</span>
                      <span style={{ color: '#1890ff', fontWeight: 'bold', marginLeft: 8 }}>{questions.length}</span>
                    </div>
                    
                    <div style={{ maxHeight: 500, overflowY: 'auto' }}>
                      {questions.map((q: any, index: number) => (
                        <div 
                          key={q.id || index} 
                          style={{ 
                            marginBottom: 16, 
                            padding: 14, 
                            background: '#fafafa',
                            borderRadius: 6,
                            border: '1px solid #e8e8e8',
                            transition: 'all 0.2s',
                          }}
                          onMouseEnter={(e: React.MouseEvent<HTMLDivElement>) => {
                            e.currentTarget.style.background = '#f0f0f0';
                            e.currentTarget.style.borderColor = '#1890ff';
                          }}
                          onMouseLeave={(e: React.MouseEvent<HTMLDivElement>) => {
                            e.currentTarget.style.background = '#fafafa';
                            e.currentTarget.style.borderColor = '#e8e8e8';
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: 8 }}>
                            <span style={{ 
                              display: 'inline-block',
                              width: 24,
                              height: 24,
                              lineHeight: '24px',
                              textAlign: 'center',
                              background: '#1890ff',
                              color: '#fff',
                              borderRadius: '50%',
                              fontSize: 12,
                              fontWeight: 'bold',
                              marginRight: 12,
                              flexShrink: 0
                            }}>
                              {q.id || (index + 1)}
                            </span>
                            <p style={{ fontWeight: 'bold', margin: 0, flex: 1, fontSize: 14 }}>
                              {q.question || q.content || q.title || '题目'}
                            </p>
                          </div>
                          
                          <div style={{ marginLeft: 36 }}>
                            {q.type && (
                              <Tag color="blue" style={{ marginBottom: 4 }}>
                                {q.type}
                              </Tag>
                            )}
                            {q.category && (
                              <Tag color="cyan" style={{ marginBottom: 4, marginLeft: 4 }}>
                                {q.category}
                              </Tag>
                            )}
                            {q.difficulty && (
                              <Tag 
                                color={q.difficulty === '简单' ? 'green' : q.difficulty === '中等' ? 'orange' : 'red'}
                                style={{ marginBottom: 4, marginLeft: 4 }}
                              >
                                难度: {q.difficulty}
                              </Tag>
                            )}
                            
                            {(q.reference_answer || q.answer) && (
                              <div style={{ 
                                marginTop: 12, 
                                padding: 10, 
                                background: '#f6ffed', 
                                borderRadius: 4,
                                borderLeft: '3px solid #52c41a'
                              }}>
                                <div style={{ fontSize: 12, color: '#52c41a', fontWeight: 'bold', marginBottom: 4 }}>
                                  💡 参考答案：
                                </div>
                                <div style={{ color: '#333', lineHeight: 1.6, fontSize: 13 }}>
                                  {q.reference_answer || q.answer}
                                </div>
                              </div>
                            )}
                            
                            {q.scoring_points && Array.isArray(q.scoring_points) && q.scoring_points.length > 0 && (
                              <div style={{ 
                                marginTop: 12, 
                                padding: 10, 
                                background: '#fff7e6', 
                                borderRadius: 4,
                                borderLeft: '3px solid #fa8c16'
                              }}>
                                <div style={{ fontSize: 12, color: '#fa8c16', fontWeight: 'bold', marginBottom: 6 }}>
                                  📝 评分要点：
                                </div>
                                <ul style={{ margin: 0, paddingLeft: 20, color: '#333', fontSize: 12 }}>
                                  {q.scoring_points.map((point: string, idx: number) => (
                                    <li key={idx} style={{ marginBottom: 4 }}>{point}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              ) : null;
            })()}
            
            {/* {(currentApp as any).resume_text && (
              <Card 
                title="📄 简历内容" 
                size="small" 
                style={{ marginTop: 16 }}
                headStyle={{ background: '#f5f5f5' }}
              >
                <div style={{ 
                  maxHeight: 300, 
                  overflowY: 'auto', 
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.6
                }}>
                  {(currentApp as any).resume_text}
                </div>
              </Card>
            )} */}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AdminApplicationManagement;
