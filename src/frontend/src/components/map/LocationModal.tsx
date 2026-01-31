import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogActions,
  DialogContent,
  Button,
  Input,
  Label,
  Textarea,
  Dropdown,
  Option,
} from '@fluentui/react-components';
import type { MapLocation, MapLocationCreate, MapLocationUpdate } from '../../types/mapLocation';
import { LocationType, LocationTypeLabels } from '../../types/locationType';

interface LocationModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (data: MapLocationCreate | MapLocationUpdate) => Promise<void>;
  initialCoords?: [number, number];
  editingLocation?: MapLocation;
}

export default function LocationModal({
  open,
  onClose,
  onSave,
  initialCoords,
  editingLocation,
}: LocationModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [locationType, setLocationType] = useState<LocationType>(LocationType.OTHER);
  const [saving, setSaving] = useState(false);

  // Initialize form when modal opens
  useEffect(() => {
    if (open) {
      if (editingLocation) {
        setName(editingLocation.name);
        setDescription(editingLocation.description || '');
        setLatitude(editingLocation.latitude.toString());
        setLongitude(editingLocation.longitude.toString());
        setLocationType(editingLocation.icon_type || LocationType.OTHER);
      } else if (initialCoords) {
        setName('');
        setDescription('');
        setLatitude(initialCoords[0].toFixed(6));
        setLongitude(initialCoords[1].toFixed(6));
        setLocationType(LocationType.OTHER);
      }
    }
  }, [open, editingLocation, initialCoords]);

  const handleSave = async () => {
    if (!name.trim() || !latitude || !longitude) {
      alert('Name, latitude, and longitude are required');
      return;
    }

    setSaving(true);
    try {
      const data: MapLocationCreate | MapLocationUpdate = {
        name: name.trim(),
        description: description.trim() || undefined,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        icon_type: locationType,
      };

      await onSave(data);
      onClose();
    } catch (error) {
      console.error('Error saving location:', error);
      alert(`Failed to save location: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (!saving) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={(_, data) => !saving && data.open === false && handleClose()}>
      <DialogSurface>
        <DialogBody>
          <DialogTitle>{editingLocation ? 'Edit Location' : 'Add New Location'}</DialogTitle>
          <DialogContent style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <Label htmlFor="name" required>
                Name
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Dragon's Lair"
                disabled={saving}
              />
            </div>

            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description..."
                disabled={saving}
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="locationType">Location Type</Label>
              <Dropdown
                id="locationType"
                value={LocationTypeLabels[locationType]}
                selectedOptions={[locationType]}
                onOptionSelect={(_, data) => setLocationType(data.optionValue as LocationType)}
                disabled={saving}
              >
                {Object.entries(LocationTypeLabels).map(([value, label]) => (
                  <Option key={value} value={value} text={label}>
                    {label}
                  </Option>
                ))}
              </Dropdown>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <Label htmlFor="latitude" required>
                  Latitude
                </Label>
                <Input
                  id="latitude"
                  type="number"
                  step="0.000001"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  disabled={saving}
                />
              </div>

              <div>
                <Label htmlFor="longitude" required>
                  Longitude
                </Label>
                <Input
                  id="longitude"
                  type="number"
                  step="0.000001"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  disabled={saving}
                />
              </div>
            </div>
          </DialogContent>
          <DialogActions>
            <Button appearance="secondary" onClick={handleClose} disabled={saving}>
              Cancel
            </Button>
            <Button appearance="primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save'}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}
