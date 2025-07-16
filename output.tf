output "instance_public_ip" {
	description = "public IP address of the Ec2 instance"
	value = aws_instance.Chat_Server.public_ip
}
