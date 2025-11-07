const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const sqlite3 = require('sqlite3');
const { open } = require('sqlite');
const path = require('path');
const cors = require('cors');
const cookieParser = require('cookie-parser');
const { MongoClient, ObjectId } = require('mongodb');

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// MongoDB 连接配置
const mongoUri = 'mongodb://localhost:27017';
const dbName = 'psychology_analysis';
const collectionName = 'analysis_records';

// Middleware
app.use(express.json());
app.use(cookieParser());
app.use(cors({
    origin: true, // 允许所有来源，生产环境中应该设置具体的域名
    credentials: true // 允许跨域发送cookies
}));

// 数据库连接
let db;
(async () => {
    db = await open({
        filename: path.join(__dirname, 'auth.db'),
        driver: sqlite3.Database
    });

    // 初始化数据库表
    await db.exec(`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            roles TEXT DEFAULT 'editor',
            is_active BOOLEAN DEFAULT true
        )
    `);

    // 分析结果表初始化
    await db.exec(`
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL,
            timestamp VARCHAR(50),
            imageBase64 TEXT,
            questionnaire TEXT,
            imageAnalysisResult TEXT,
            questionnaireResult TEXT,
            cozeParams TEXT,
            deepseekParams TEXT
        )
    `);
})();

// 中间件：验证JWT token
const authenticateToken = (req, res, next) => {
    const token = req.cookies.token || req.headers.authorization?.split(' ')[1];

    if (!token) {
        return res.status(401).json({ message: '未提供认证token' });
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({ message: 'token无效或已过期' });
        }
        req.user = user;
        next();
    });
};

// 注册路由
app.post('/api/auth/register', async (req, res) => {
    try {
        const { username, password, email, verify} = req.body;

        // 验证输入
        if (!username || !password || !email) {
            return res.status(400).json({ message: '用户名、密码和邮箱都是必填的' });
        }
        if (verify != "Linyuye2025") {
            return res.status(400).json({ message: '邀请码错误' });
        }
        // 检查用户名是否已存在
        const existingUser = await db.get('SELECT id FROM users WHERE username = ?', [username]);
        if (existingUser) {
            return res.status(400).json({ message: '用户名已存在' });
        }

        // 检查邮箱是否已存在
        const existingEmail = await db.get('SELECT id FROM users WHERE email = ?', [email]);
        if (existingEmail) {
            return res.status(400).json({ message: '邮箱已被使用' });
        }

        // 加密密码
        const hashedPassword = await bcrypt.hash(password, 10);

        // 创建新用户
        await db.run(
            'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
            [username, hashedPassword, email]
        );

        res.status(201).json({ message: '注册成功' });

        // 获取当前时间
        const now = new Date().toISOString(); // 格式：2025-08-23T04:30:12.123Z

        // 获取客户端 IP
        const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;

        // 打印日志
        console.log(`[${now}] 注册账户: ${username}, IP: ${ip}`);

    } catch (error) {
        console.error('注册错误:', error);
        res.status(500).json({ message: '服务器错误' });
    }
});

// 登录路由
app.post('/api/auth/login', async (req, res) => {
    try {
        const { username, password } = req.body;

        // 查找用户
        const user = await db.get('SELECT * FROM users WHERE username = ?', [username]);
        if (!user) {
            return res.status(401).json({ message: '用户名或密码错误' });
        }

        // 验证密码
        const validPassword = await bcrypt.compare(password, user.password);
        if (!validPassword) {
            return res.status(401).json({ message: '用户名或密码错误' });
        }

        // 更新最后登录时间
        await db.run(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            [user.id]
        );

        // 生成JWT token
        const token = jwt.sign(
            { 
                id: user.id, 
                username: user.username,
                roles: user.roles.split(',')
            },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        // 设置cookie
        res.cookie('token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 24 * 60 * 60 * 1000 // 24小时
        });

        res.json({
            message: '登录成功',
            user: {
                id: user.id,
                username: user.username,
                email: user.email,
                roles: user.roles.split(',')
            },
            token
        });
    } catch (error) {
        console.error('登录错误:', error);
        res.status(500).json({ message: '服务器错误' });
    }
});

// 登出路由
app.post('/api/auth/logout', authenticateToken, (req, res) => {
    res.clearCookie('token');
    res.json({ message: '登出成功' });
});

// 获取当前用户信息
app.get('/api/auth/me', authenticateToken, async (req, res) => {
    try {
        const user = await db.get(
            'SELECT id, username, email, roles, created_at, last_login FROM users WHERE id = ?',
            [req.user.id]
        );

        if (!user) {
            return res.status(404).json({ message: '用户不存在' });
        }

        res.json({
            user: {
                ...user,
                roles: user.roles.split(',')
            }
        });
    } catch (error) {
        console.error('获取用户信息错误:', error);
        res.status(500).json({ message: '服务器错误' });
    }
});

// 保存分析结果
app.post('/api/saveAnalysis', async (req, res) => {
    try {
        const data = req.body;
        const stmt = await db.run(
            `INSERT INTO analysis_history (username, timestamp, imageBase64, questionnaire, imageAnalysisResult, questionnaireResult, cozeParams, deepseekParams)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
            [
                data.id || data.username,
                data.timestamp,
                data.imageBase64,
                JSON.stringify(data.questionnaire),
                JSON.stringify(data.imageAnalysisResult),
                JSON.stringify(data.questionnaireResult),
                JSON.stringify(data.cozeParams),
                JSON.stringify(data.deepseekParams)
            ]
        );
        res.json({ success: true, insertedId: stmt.lastID });
    } catch (error) {
        console.error('保存分析结果错误:', error);
        res.status(500).json({ success: false, error: '保存失败' });
    }
});

// 获取历史记录 - 从 MongoDB 获取
app.get('/api/history', async (req, res) => {
    const client = new MongoClient(mongoUri);
    try {
        const { username } = req.query;
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection(collectionName);
        
        // 从 MongoDB 查询该用户的分析记录
        const records = await collection.find({ id: username })
            .sort({ timestamp: -1 })
            .toArray();        // 转换数据格式以适配前端显示
        const history = records.map(item => {
            // 处理缩略图
            let thumbnail = '';
            if (item.imageBase64) {
                // 如果是完整的base64（包含data:前缀），截取一部分作为缩略图
                // 如果没有前缀，保持原样
                if (item.imageBase64.startsWith('data:')) {
                    // 为了减少数据量，只截取前1000个字符作为缩略图
                    const prefix = item.imageBase64.substring(0, item.imageBase64.indexOf(',') + 1);
                    const base64Data = item.imageBase64.substring(item.imageBase64.indexOf(',') + 1);
                    // 只取base64字符串的前面一部分，足够显示小缩略图
                    thumbnail = prefix + base64Data.substring(0, 1000);
                } else {
                    // 如果原始数据没有前缀，加上前缀
                    thumbnail = 'data:image/png;base64,' + item.imageBase64.substring(0, 1000);
                }
            }
            
            return {
                id: item._id.toString(), // 这是 MongoDB ObjectId，用于查看详情
                _id: item._id.toString(), // 保留 _id 字段，以便前端使用
                userId: item.id, // 这是用户名
                date: item.timestamp,
                thumbnail: thumbnail,
                questionType: (() => {
                    try {
                        if (item.questionnaire && typeof item.questionnaire === 'object') {
                            return Object.keys(item.questionnaire).join(',');
                        }
                        return '未分类';
                    } catch { 
                        return '未分类'; 
                    }
                })(),
                ...item
            };
        });
        
        res.json(history);
    } catch (error) {
        console.error('获取历史记录错误:', error);
        res.status(500).json([]);
    } finally {
        await client.close();
    }
});

// 删除历史记录 - 从 MongoDB 删除
app.delete('/api/history/:id', async (req, res) => {
    const client = new MongoClient(mongoUri);
    try {
        const { id } = req.params;
        
        console.log('删除历史记录，ID:', id);
        
        // 验证 ObjectId 格式
        if (!ObjectId.isValid(id)) {
            console.error('无效的MongoDB ObjectId:', id);
            return res.status(400).json({ success: false, error: '无效的记录ID格式' });
        }
        
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection(collectionName);
        
        // 从 MongoDB 删除记录
        const result = await collection.deleteOne({ 
            _id: new ObjectId(id) 
        });
        
        if (result.deletedCount > 0) {
            console.log('成功删除记录:', id);
            res.json({ success: true });
        } else {
            console.error('要删除的记录不存在, ID:', id);
            res.status(404).json({ success: false, error: '记录不存在' });
        }
    } catch (error) {
        console.error('删除历史记录错误:', error);
        res.status(500).json({ success: false, error: '删除失败' });
    } finally {
        await client.close();
    }
});

// 获取单个历史记录详情 - 从 MongoDB 获取
app.get('/api/history/detail/:id', async (req, res) => {
    const client = new MongoClient(mongoUri);
    try {
        const { id } = req.params;
        
        console.log('获取历史记录详情，ID:', id);
        
        // 验证 ObjectId 格式
        if (!ObjectId.isValid(id)) {
            console.error('无效的MongoDB ObjectId:', id);
            return res.status(400).json({ error: '无效的记录ID格式' });
        }
        
        await client.connect();
        const db = client.db(dbName);
        const collection = db.collection(collectionName);
        
        // 从 MongoDB 查询具体记录
        const record = await collection.findOne({ 
            _id: new ObjectId(id) 
        });
        
        if (record) {
            console.log('找到记录:', record._id);
            res.json(record);
        } else {
            console.error('记录不存在, ID:', id);
            res.status(404).json({ error: '记录不存在' });
        }
    } catch (error) {
        console.error('获取历史记录详情错误:', error);
        res.status(500).json({ error: '获取失败' });
    } finally {
        await client.close();
    }
});

// 提供静态文件服务
app.use(express.static(path.join(__dirname)));

// 启动服务器
app.listen(PORT, () => {
    console.log(`认证服务器运行在端口 ${PORT}`);
});
