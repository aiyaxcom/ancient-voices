/**
 * Ancient Voices API Client
 * 历史人物沉浸式对话 API 调用客户端
 */

const API_BASE = '/api/v1/wenyan';

// 通用请求方法
async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;

    const config = {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    };

    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || data.message || '请求失败');
    }

    return data;
}

// Ancient Voices API
const wenyanAPI = {
    /**
     * 获取场景列表
     */
    async listScenarios() {
        return request('/scenarios');
    },

    /**
     * 获取场景详情
     */
    async getScenario(scenarioId) {
        return request(`/scenarios/${scenarioId}`);
    },

    /**
     * 创建会话
     */
    async createSession(data) {
        return request('/sessions', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    /**
     * 获取会话详情
     */
    async getSession(sessionId) {
        return request(`/sessions/${sessionId}`);
    },

    /**
     * 获取会话的消息历史
     */
    async getSessionMessages(sessionId) {
        return request(`/sessions/${sessionId}/messages`);
    },

    /**
     * 发送消息并获取回复
     */
    async chat(sessionId, message) {
        return request(`/sessions/${sessionId}/chat`, {
            method: 'POST',
            body: JSON.stringify({
                message: message,
            }),
        });
    },

    /**
     * 发送消息并获取流式回复
     */
    async chatStream(sessionId, message, onChunk, onDone, onError) {
        const url = `${API_BASE}/sessions/${sessionId}/chat/stream`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    message: message,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                onError(errorData.detail || '请求失败');
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        if (dataStr === '[DONE]') {
                            onDone();
                            continue;
                        }
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.content) {
                                onChunk(data.content);
                            }
                            if (data.error) {
                                onError(data.error);
                            }
                        } catch (e) {
                            // JSON 解析失败，忽略
                        }
                    }
                }
            }
        } catch (e) {
            onError(e.message || '网络错误');
        }
    },

    /**
     * 创建反思报告
     */
    async createReport(sessionId, agentId = null) {
        return request(`/sessions/${sessionId}/reports`, {
            method: 'POST',
            body: JSON.stringify({
                agent_id: agentId,
            }),
        });
    },

    /**
     * 查询报告状态和内容
     */
    async getReport(reportId) {
        return request(`/reports/${reportId}`);
    },

    /**
     * 获取会话的所有报告列表
     */
    async listSessionReports(sessionId) {
        return request(`/sessions/${sessionId}/reports`);
    },

    /**
     * 保存创建的场景
     */
    async saveScenario(scenario, agents) {
        return request('/scenarios/create', {
            method: 'POST',
            body: JSON.stringify({
                scenario: scenario,
                agents: agents,
            }),
        });
    },
};

// 导出
window.wenyanAPI = wenyanAPI;