import { 
    Box, 
    Typography, 
    Button, 
    Grid, 
    Card, 
    CardContent, 
    CardMedia, 
    Container,
    useTheme,
    useMediaQuery
  } from '@mui/material';
  import { Link } from 'react-router-dom';
  import { useAuth } from '../AuthContext';
  import heroImage from '../assets/hero-image.jpg'; // Replace with your image
  
  const features = [
    {
      title: "Task Management",
      description: "Organize your tasks with drag-and-drop functionality and priority levels.",
      icon: "📝"
    },
    {
      title: "Secure Authentication",
      description: "Protected with JWT and password hashing for maximum security.",
      icon: "🔒"
    },
    {
      title: "Cross-Device Sync",
      description: "Access your tasks from any device with real-time updates.",
      icon: "📱"
    }
  ];
  
  export default function Home() {
    const { isAuthenticated } = useAuth();
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
    return (
      <Box sx={{ flexGrow: 1 }}>
        {/* Hero Section */}
        <Box 
          sx={{ 
            backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.5), url(${heroImage})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            color: 'white',
            py: 10,
            textAlign: 'center'
          }}
        >
          <Container maxWidth="md">
            <Typography 
              variant={isMobile ? "h3" : "h2"} 
              component="h1" 
              gutterBottom
              sx={{ fontWeight: 'bold' }}
            >
              Welcome to TaskMaster Pro
            </Typography>
            <Typography variant="h5" sx={{ mb: 4 }}>
              The ultimate productivity tool for managing your daily tasks
            </Typography>
            {!isAuthenticated && (
              <Button 
                component={Link} 
                to="/register" 
                variant="contained" 
                size="large"
                sx={{ 
                  mr: 2,
                  backgroundColor: 'primary.main',
                  '&:hover': { backgroundColor: 'primary.dark' }
                }}
              >
                Get Started
              </Button>
            )}
            <Button 
              component={Link} 
              to={isAuthenticated ? "/tasks" : "/login"} 
              variant="outlined" 
              size="large"
              sx={{ 
                color: 'white',
                borderColor: 'white',
                '&:hover': { borderColor: 'white' }
              }}
            >
              {isAuthenticated ? "Go to Dashboard" : "Login"}
            </Button>
          </Container>
        </Box>
  
        {/* Features Section */}
        <Container maxWidth="lg" sx={{ py: 8 }}>
          <Typography 
            variant="h4" 
            align="center" 
            gutterBottom 
            sx={{ fontWeight: 'medium', mb: 6 }}
          >
            Why Choose TaskMaster?
          </Typography>
          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card 
                  sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    transition: 'transform 0.3s',
                    '&:hover': { transform: 'scale(1.03)' }
                  }}
                >
                  <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                    <Typography variant="h2" sx={{ mb: 2 }}>
                      {feature.icon}
                    </Typography>
                    <Typography gutterBottom variant="h5" component="h3">
                      {feature.title}
                    </Typography>
                    <Typography>
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
  
        {/* Call-to-Action Section */}
        <Box sx={{ backgroundColor: theme.palette.grey[100], py: 8 }}>
          <Container maxWidth="md" sx={{ textAlign: 'center' }}>
            <Typography variant="h4" gutterBottom sx={{ fontWeight: 'medium' }}>
              Ready to boost your productivity?
            </Typography>
            <Typography variant="body1" sx={{ mb: 4 }}>
              Join thousands of users who are getting more done every day.
            </Typography>
            <Button 
              component={Link} 
              to={isAuthenticated ? "/tasks" : "/register"} 
              variant="contained" 
              size="large"
              sx={{ 
                px: 6,
                py: 1.5,
                fontSize: '1.1rem'
              }}
            >
              {isAuthenticated ? "Continue to App" : "Sign Up Free"}
            </Button>
          </Container>
        </Box>
      </Box>
    );
  }