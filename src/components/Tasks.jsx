import { useState, useEffect } from 'react';
import api from '../api';
import {
  Container,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  IconButton,
  TextField,
  Button,
  Box,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState('');

  useEffect(() => {
    const fetchTasks = async () => {
      const res = await api.get('/tasks');
      setTasks(res.data.tasks);
    };
    fetchTasks();
  }, []);

  const handleAddTask = async () => {
    const res = await api.post('/tasks', { title: newTask });
    setTasks([...tasks, res.data.task]);
    setNewTask('');
  };

  const handleDeleteTask = async (id) => {
    await api.delete(`/tasks/${id}`);
    setTasks(tasks.filter((task) => task.id !== id));
  };

  const handleUpdateTask = async (id, updatedTask) => {
    const res = await api.put(`/tasks/${id}`, updatedTask);
    setTasks(tasks.map((task) => (task.id === id ? res.data.task : task)));
  };

  return (
    <Container>
      <Box sx={{ mt: 4 }}>
        <TextField
          fullWidth
          label="New Task"
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
        />
        <Button onClick={handleAddTask} variant="contained" sx={{ mt: 2 }}>
          Add Task
        </Button>
        <List>
          {tasks.map((task) => (
            <ListItem key={task.id}>
              <Checkbox
                checked={task.done}
                onChange={() =>
                  handleUpdateTask(task.id, { ...task, done: !task.done })
                }
              />
              <TextField
                value={task.title}
                onChange={(e) =>
                  handleUpdateTask(task.id, { ...task, title: e.target.value })
                }
              />
              <IconButton onClick={() => handleDeleteTask(task.id)}>
                <DeleteIcon />
              </IconButton>
            </ListItem>
          ))}
        </List>
      </Box>
    </Container>
  );
}