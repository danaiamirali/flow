# Flow
Given the traffic logs of a website (dummy website located in `website/`), served in real-time via Kafka streams, Flow uses Spark to process these data streams and store them in a Data Lake (S3). Flow predicts future traffic volume with updated and consistently deployed models trained on data from the Data Lake. 
