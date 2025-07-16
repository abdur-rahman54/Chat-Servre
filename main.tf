# Provider Block
provider "aws" {
	profile = "default"
	region = "ap-southeast-1"
	}

# Resource block
resource "aws_instance" "Chat_Server" {
	ami = "ami-02c7683e4ca3ebf58"
	instance_type = "t2.micro"

	tags = {
		Name = "TerraformChatServer"
	}
}
