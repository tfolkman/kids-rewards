import React, { useState } from 'react';
import * as api from '../services/api';

const AwardPoints: React.FC = () => {
    const [kidUsername, setKidUsername] = useState('');
    const [points, setPoints] = useState<number | ''>('');
    const [reason, setReason] = useState('');
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setMessage(null);
        setError(null);

        if (points === '' || points <= 0) {
            setError("Points must be a positive number.");
            return;
        }

        const awardData: api.PointsAwardData = {
            kid_username: kidUsername,
            points: Number(points),
            reason: reason || undefined,
        };

        try {
            const response = await api.awardPoints(awardData);
            setMessage(`Successfully awarded ${points} points to ${response.data.username}. New balance: ${response.data.points}`);
            setKidUsername('');
            setPoints('');
            setReason('');
        } catch (err: any) {
            console.error("Error awarding points:", err);
            setError(err.response?.data?.detail || "Failed to award points.");
        }
    };

    return (
        <div>
            <h3>Award Points to Kid</h3>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Kid's Username: </label>
                    <input 
                        type="text" 
                        value={kidUsername} 
                        onChange={(e) => setKidUsername(e.target.value)} 
                        required 
                    />
                </div>
                <div>
                    <label>Points to Award: </label>
                    <input 
                        type="number" 
                        value={points} 
                        onChange={(e) => setPoints(e.target.value === '' ? '' : Number(e.target.value))} 
                        required 
                        min="1"
                    />
                </div>
                <div>
                    <label>Reason (Optional): </label>
                    <input 
                        type="text" 
                        value={reason} 
                        onChange={(e) => setReason(e.target.value)} 
                    />
                </div>
                <button type="submit">Award Points</button>
            </form>
            {message && <p style={{ color: 'green' }}>{message}</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
    );
};

export default AwardPoints;