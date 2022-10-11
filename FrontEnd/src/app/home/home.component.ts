import { HttpClient } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../_services/auth.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {

  constructor(private auth:AuthService,private http:HttpClient,private route:Router) { }

  ngOnInit(): void {
	this.auth.canAccess();
  }
  files: File[] = [];
  data= false;

	onSelect(event: { addedFiles: any; }) {
		console.log(event);
		this.files.push(...event.addedFiles);
	}

	onRemove(event: File) {
		console.log(event);
		this.files.splice(this.files.indexOf(event), 1);
	}
  
	addData(val:any){
		let formData  = new FormData();
		formData.append('file', this.files[0], this.files[0].name);
		this.http.post('http://127.0.0.1:5000/data', formData).subscribe(response => {
			console.log(response)
    		this.data = true;
		});


	}

	onPredict(data:{timeperiod:number}){
		this.http.post('http://127.0.0.1:5000/predict',data).subscribe(response=>{
			console.log(response)
			this.route.navigate(['/dashboard']);
			this.data=false;
		})
	}
}
