import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'Hubspot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            const formData = new FormData();

            if (integrationType === "Hubspot") {
                formData.append("user_id", credentials?.user_id || "default-user");
            } else {
                formData.append("credentials", JSON.stringify(credentials));
            }

            const response = await axios.post(
                `http://localhost:8000/integrations/${endpoint}/load`,
                formData
            );

            const data = response.data;
            setLoadedData(JSON.stringify(data, null, 2));
        } catch (e) {
            alert(e?.response?.data?.detail || "Failed to load data");
        }
    };

    return (
        <Box
            display='flex'
            justifyContent='center'
            alignItems='center'
            flexDirection='column'
            width='100%'
            p={2}
        >
            <Box display='flex' flexDirection='column' width='100%' maxWidth='800px'>
                <TextField
                    label="Loaded Data"
                    value={loadedData || ''}
                    sx={{ mt: 2, width: '100%' }}
                    InputLabelProps={{ shrink: true }}
                    disabled
                    multiline
                    rows={15}
                    inputProps={{
                        style: {
                            fontFamily: 'monospace',
                            fontSize: '12px'
                        }
                    }}
                />

                <Button
                    onClick={handleLoad}
                    sx={{ mt: 2 }}
                    variant='contained'
                >
                    Load Data
                </Button>

                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{ mt: 1 }}
                    variant='contained'
                >
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
};