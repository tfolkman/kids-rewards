import React, { useState, useEffect } from 'react';
import * as api from '../services/api';

const ManageStoreItems: React.FC = () => {
    const [items, setItems] = useState<api.StoreItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Form state for adding/editing items
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const [currentItemId, setCurrentItemId] = useState<string | null>(null);
    const [itemName, setItemName] = useState('');
    const [itemDescription, setItemDescription] = useState('');
    const [itemPoints, setItemPoints] = useState<number | ''>('');

    const fetchItems = async () => {
        setIsLoading(true);
        try {
            const response = await api.getStoreItems();
            setItems(response.data);
            setError(null);
        } catch (err) {
            console.error("Error fetching store items:", err);
            setError("Failed to load store items.");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, []);

    const resetForm = () => {
        setIsEditing(false);
        setCurrentItemId(null);
        setItemName('');
        setItemDescription('');
        setItemPoints('');
    };

    const handleEdit = (item: api.StoreItem) => {
        setIsEditing(true);
        setCurrentItemId(item.id);
        setItemName(item.name);
        setItemDescription(item.description || '');
        setItemPoints(item.points_cost);
    };

    const handleDelete = async (itemId: string) => {
        if (window.confirm("Are you sure you want to delete this item?")) {
            try {
                await api.deleteStoreItem(itemId);
                fetchItems(); // Refresh list
            } catch (err) {
                console.error("Error deleting item:", err);
                setError("Failed to delete item.");
            }
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (itemPoints === '' || itemPoints <= 0) {
            setError("Points must be a positive number.");
            return;
        }
        const itemData: api.StoreItemCreate = {
            name: itemName,
            description: itemDescription,
            points_cost: Number(itemPoints),
        };

        try {
            if (isEditing && currentItemId) {
                await api.updateStoreItem(currentItemId, itemData);
            } else {
                await api.createStoreItem(itemData);
            }
            resetForm();
            fetchItems(); // Refresh list
        } catch (err: any) {
            console.error("Error saving item:", err);
            setError(err.response?.data?.detail || "Failed to save item.");
        }
    };

    if (isLoading) return <p>Loading store items...</p>;
    if (error) return <p style={{ color: 'red' }}>{error}</p>;

    return (
        <div>
            <h3>{isEditing ? 'Edit Store Item' : 'Add New Store Item'}</h3>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Name: </label>
                    <input type="text" value={itemName} onChange={(e) => setItemName(e.target.value)} required />
                </div>
                <div>
                    <label>Description (Optional): </label>
                    <input type="text" value={itemDescription} onChange={(e) => setItemDescription(e.target.value)} />
                </div>
                <div>
                    <label>Points Cost: </label>
                    <input type="number" value={itemPoints} onChange={(e) => setItemPoints(e.target.value === '' ? '' : Number(e.target.value))} required min="1" />
                </div>
                <button type="submit">{isEditing ? 'Update Item' : 'Add Item'}</button>
                {isEditing && <button type="button" onClick={resetForm} style={{ marginLeft: '10px' }}>Cancel Edit</button>}
            </form>

            <hr style={{ margin: '20px 0' }}/>

            <h3>Current Store Items</h3>
            {items.length === 0 ? <p>No items in store yet.</p> : (
                <ul style={{ listStyleType: 'none', padding: 0 }}>
                    {items.map(item => (
                        <li key={item.id} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
                            <strong>{item.name}</strong> ({item.points_cost} points)
                            <p>{item.description || 'No description'}</p>
                            <button onClick={() => handleEdit(item)} style={{ marginRight: '5px' }}>Edit</button>
                            <button onClick={() => handleDelete(item.id)}>Delete</button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default ManageStoreItems;