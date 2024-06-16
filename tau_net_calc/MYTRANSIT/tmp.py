def correct_repeated_stops_in_trips(self):
    self.stop_times_df = self.stop_times_df.set_index(['trip_id', 'stop_sequence'])

    self.parent.setMessage(f'Correcting repeated stops...')
    QApplication.processEvents()

    self.merged_df = pd.merge(self.routes_df, self.trips_df, on="route_id")
    self.merged_df = pd.merge(self.merged_df, self.stop_times_df.reset_index(), on="trip_id")

    self.parent.setMessage(f'Grouping ...')
    QApplication.processEvents()

    grouped = self.merged_df.groupby('route_id')

    self.max_stop_id = self.stop_df['stop_id'].max()

    all_routes = len(grouped)
    count = 0

    new_stops = []
    for route_id, group in grouped:
        count += 1
        if count % 100 == 0:
            self.parent.setMessage(f'Correcting repeated stops. Processing route {count} of {all_routes}')
            QApplication.processEvents()

        first_trip_id = group['trip_id'].iloc[0]  
        trip = self.stop_times_df.xs(first_trip_id, level='trip_id').reset_index()
        stop_ids = []

        for index, row in trip.iterrows():
            stop_id = row['stop_id']
            stop_sequence = row['stop_sequence']

            if stop_id in stop_ids:
                new_stop_id = self.create_new_stop(stop_id)
                new_stops.append((route_id, stop_sequence, new_stop_id))
            else:
                stop_ids.append(stop_id)

    count = 0
    len_stops = len(new_stops)

    # Optimize the stop replacement by bulk operation
    if new_stops:
        new_stops_df = pd.DataFrame(new_stops, columns=['route_id', 'stop_sequence', 'new_stop_id'])

        # Merge with stop_times_df to identify rows to update
        stops_to_update = self.merged_df.merge(new_stops_df, on=['route_id', 'stop_sequence'], how='inner')
        
        # Update the stop_ids in bulk
        for _, row in stops_to_update.iterrows():
            self.stop_times_df.loc[(row['trip_id'], row['stop_sequence']), 'stop_id'] = row['new_stop_id']
            count += 1
            if count % 3 == 0:
                self.parent.setMessage(f'Correcting repeated stops. Replacing stop {count} of {len_stops}')
                QApplication.processEvents()

def inplace_new_stop_on_all_trips(self, route_id, stop_sequence, new_stop_id):
    trip_ids = self.merged_df[self.merged_df["route_id"] == route_id]["trip_id"].unique()
    filter_condition = self.stop_times_df.index.get_level_values('trip_id').isin(trip_ids) & (self.stop_times_df.index.get_level_values('stop_sequence') == stop_sequence)
    self.stop_times_df.loc[filter_condition, "stop_id"] = new_stop_id
